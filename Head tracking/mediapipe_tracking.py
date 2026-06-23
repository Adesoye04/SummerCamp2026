#!/usr/bin/env python3

import os
os.environ["OPENCV_VIDEOIO_PRIORITY_QT"] = "0"
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"
import cv2
import rospy
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import Image
from threading import Lock
import math
from cv_bridge import CvBridge
import mediapipe as mp
import matplotlib.pyplot as plt

"""
Add this to start_background_thread method in HRI research code:

# 1. Initialize your HeadFollower (False = no window, True = show window)
follower = HeadFollower(use_viz=True) 

# 2. Start it in its own background thread
tracking_thread = Thread(target=follower.run_service, daemon=True)
tracking_thread.start()

"""

class HeadFollower:
    def __init__(self, use_viz=False, camera_topic="/camera/color/image_raw"):
        self.lock = Lock()
        self.is_active = True
        self.latest_frame = None
        self.use_viz = use_viz
        self._ros_initialized = False  # Guard for ROS calls
        self.last_person_seen_time = 0.0

        # --- Tuning Constants ---
        self.GAIN_YAW = 10
        self.GAIN_PITCH = 6
        self.DEADZONE = 0.01
        self.PITCH_OFFSET = 3.0
        self.TIMEOUT_STOP = 2.0
        self.TIMEOUT_RESET = 5.0
        self.TIMEOUT_PATROL = 12.0

        self.last_yaw = 0.0
        self.last_pitch = 0.0
        # FIX: Don't call rospy.get_time() here - will be set in run_service()
        self.last_callback_time = 0.0

        # --- MediaPipe Pose Setup ---
        self.bridge = CvBridge()
        self.mp_pose = mp.solutions.pose
        self.pose_detector = self.mp_pose.Pose(
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # --- ROS Setup ---
        self.sub = rospy.Subscriber(camera_topic, Image, self.image_callback, queue_size=1)
        self.head_pub = rospy.Publisher("/qt_robot/head_position/command", Float64MultiArray, queue_size=1)

        # --- Visualization ---
        if self.use_viz:
            rospy.loginfo("Visualization ENABLED")
        else:
            rospy.loginfo("Visualization DISABLED")

    def image_callback(self, msg):
        with self.lock:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            self.last_callback_time = rospy.get_time()

    def update(self):
            if not self.is_active:
                return "PAUSED"

            now = rospy.get_time()
            with self.lock:
                frame = self.latest_frame
                
            time_since_person = now - self.last_person_seen_time

            # Run the pose processor to see if anyone is there
            self.track_pose(frame)

            # STATE 1: We are actively tracking (Person seen < 2 seconds ago)
            if time_since_person < self.TIMEOUT_STOP:
                state = "TRACKING"
                # track_pose already handled the movement

            # STATE 2: Person just left (Seen between 2 and 7 seconds ago)
            elif time_since_person < self.TIMEOUT_RESET:
                state = "CENTERING"
                self.drift_to_center()

            # STATE 3: Giving up (Seen more than 7 seconds ago)
            elif time_since_person < self.TIMEOUT_PATROL:
                state = "PATROLLING"
                self.patrol_search(now)
            
            else:
                return None

            return state

    def track_pose(self, frame):
        if frame is None:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose_detector.process(rgb)

        if results.pose_landmarks:
            self.last_person_seen_time = rospy.get_time()

            # Use the nose as head reference
            nose = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
            body_cx = nose.x
            body_cy = nose.y

            # Update head positions
            self.last_yaw += (0.5 - body_cx) * self.GAIN_YAW
            self.last_pitch += (-(0.5 - body_cy)) * self.GAIN_PITCH
            self.publish_head()

        # Visualization
        if self.use_viz:
            self.mp_drawing.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            cv2.imshow("Pose Tracking", frame)
            cv2.waitKey(1)

    def drift_to_center(self):
        self.last_yaw *= 0.95
        self.last_pitch *= 0.95
        self.publish_head()

    def patrol_search(self, current_time):
        self.last_yaw = 40.0 * math.sin(current_time * 0.5)
        self.last_pitch = -5.0
        self.publish_head()

    def publish_head(self):
        final_yaw = max(min(self.last_yaw, 60), -60)
        final_pitch = max(min(self.last_pitch + self.PITCH_OFFSET, 15), -15)
        self.head_pub.publish(Float64MultiArray(data=[final_yaw, final_pitch]))

    def reset_head(self):
        self.last_yaw, self.last_pitch = 0.0, 0.0
        self.publish_head()
    
    def reset_head_softly(self):
        for i in range(10):
            rospy.sleep(0.5)
            self.drift_to_center()
        self.last_yaw, self.last_pitch = 0.0, 0.0
        self.last_person_seen_time = 0.0
        self.publish_head()
        rospy.sleep(1.0)
        if self.is_active == False:
            self.resume()

    def stop(self):
        """Pauses tracking and releases head control."""
        with self.lock:
            self.is_active = False
        rospy.loginfo("HeadFollower: Paused")

    def resume(self):
        """Resumes tracking logic."""
        with self.lock:
            self.is_active = True
        rospy.loginfo("HeadFollower: Resumed")

    def run_service(self):
        # FIX: Initialize ROS time here after rospy.init_node() is guaranteed
        try:
            rospy.sleep(0.5)  # Reduced from 1.0s
            self.last_callback_time = rospy.get_time()  # Safe to call now
            self._ros_initialized = True
        except Exception as e:
            print(f"HeadFollower ROS init error: {e}")
            return
        
        self.reset_head()
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            try:
                current_state = self.update()
            except Exception as e:
                print(f"HeadFollower update error: {e}")
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("head_follower")
    follower = HeadFollower(use_viz=True)
    rospy.sleep(1.0)
    follower.reset_head()
    follower.run_service()
