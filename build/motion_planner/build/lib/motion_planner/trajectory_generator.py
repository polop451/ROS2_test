import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math

class TrajectoryGenerator(Node):
    def __init__(self):
        super().__init__('trajectory_generator')
        
        # สร้าง Publisher ส่งไปยัง /joint_states
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        
        # ตั้ง Timer ให้ทำงานทุกๆ 0.05 วินาที (50 มิลลิวินาที)
        self.timer_period = 0.05
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        
        # 1. กำหนดจุด Waypoints 5 จุดสำหรับข้อต่อทั้ง 4 ของเรา [joint_1, joint_2, joint_3, left_gripper_joint]
        self.waypoints = [
            [0.0,  0.0,  0.0,  0.0],   # จุดที่ 1: ท่าเริ่มต้น
            [1.57, 0.5, -0.5,  0.02],  # จุดที่ 2: หันซ้าย+กางแขน+เปิดกริปเปอร์
            [3.14, 1.0,  0.5,  0.0],   # จุดที่ 3: หันไปข้างหลัง+หดแขน+ปิดกริปเปอร์
            [-1.57, -0.5, 0.0, 0.03],  # จุดที่ 4: หันขวา+เอื้อมลงล่าง
            [0.0,  0.0,  0.0,  0.0]    # จุดที่ 5: กลับท่าเดิม
        ]
        
        self.current_waypoint_idx = 0
        self.next_waypoint_idx = 1
        self.t = 0.0  # เวลาในการควบคุมการ Interpolate (0.0 ถึง 1.0)
        self.speed = 0.02  # ความเร็วในการเคลื่อนที่ (ยิ่งน้อยยิ่งเคลื่อนที่ช้าและนุ่มนวล)

    def timer_callback(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        
        # ใส่ชื่อข้อต่อให้ตรงกับในไฟล์ URDF เป๊ะๆ
        msg.name = ['joint_1', 'joint_2', 'joint_3', 'left_gripper_joint']
        
        # ดึงจุดพิกัด ปัจจุบัน และ จุดถัดไป
        p_start = self.waypoints[self.current_waypoint_idx]
        p_end = self.waypoints[self.next_waypoint_idx]
        
        # 2. ทำ Linear Interpolation (LERP) เพื่อหาตำแหน่งนุ่มๆ ระหว่างทาง
        current_positions = []
        for i in range(len(p_start)):
            pos = p_start[i] + (p_end[i] - p_start[i]) * self.t
            current_positions.append(pos)
            
        msg.position = current_positions
        self.publisher_.publish(msg)
        
        # เพิ่มค่าเวลา t
        self.t += self.speed
        
        # ถ้าวิ่งไปถึงจุดหมาย (t >= 1.0) ให้เปลี่ยนเป้าหมายไปยังจุดถัดไป
        if self.t >= 1.0:
            self.t = 0.0
            self.current_waypoint_idx = self.next_waypoint_idx
            self.next_waypoint_idx = (self.next_waypoint_idx + 1) % len(self.waypoints)

def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryGenerator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()