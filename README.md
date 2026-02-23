<br/>
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/kern-4_dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/kern-4_light.svg">
    <img alt="kern-4" src="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/kern-4.png" width="690" height="122" style="max-width: 90%;">
  </picture>
  <br/>
  <br/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/language-Python-3776AB?&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-green">
  <img src="https://img.shields.io/badge/interface-TUI-black">
  <img src="https://img.shields.io/badge/status-Active-brightgreen">
  <img src="https://img.shields.io/badge/project-Robotics-orange">
  <img src="https://img.shields.io/badge/models-URDF-blueviolet">
  <br/>
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?logo=linux">
  <img src="https://img.shields.io/badge/platform-Windows-blue?logo=windows">
  <img src="https://img.shields.io/badge/platform-macOS-black?logo=apple">
</p>
<br/>
kern-4 is a 4DOF 3D-printed robot, including a gripper, with its URDF model and custom software for control via a terminal-based interface (TUI).

---
<img src="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/robot.png" align="right" height="350">

kern-4 is both the name of the robot and of the software that operates it. The robot uses a reducer called Planetary Drive ([more info](#planetary-drive)), to provide the actuator, in this case stepper motors, with high torque. The kern-4 software TUI is built with Python's `curses` library (preinstalled on macOS and Linux, but not on Windows for some reason...)

The entire design, which I consider modular, was created from scratch (starting with paper and pen) in [Fusion 360](https://www.autodesk.com/products/fusion-360/overview), using only the [GF Gear Generator](https://apps.autodesk.com/FUSION/en/Detail/Index?id=1236778940008086660) add-on, solely to generate the components needed for the gearbox (the sun gear, planet gears and the ring gear).

<br/>

> *"The creation of something new is not accomplished by intellect alone."*
>
> **—Carl G. Jung, Memories, Dreams, Reflections**
<br/>

---

## Installation

Create and activate a virtual environment (for PyBullet):
```bash
python -m venv kern-4
source venv/bin/activate   # On Linux or macOS
kern\Scripts\activate      # On Windows
```
Install dependencies:                                          
```bash
pip install pyserial numpy pybullet
```
*(Note: On Windows, you also need `windows-curses` to use curses)*

## Real World (kern-4)

<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/rw.png" height="300"><br>
<i>Full-profile perspective of the <br/> Kern-4 robotic arm</i>
</td>

<td align="center">
<img src="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/rw_.png" height="300"><br>
<i>Close-up side <br/> perspective of Kern-4</i>
</td>
</tr>
</table>

## Screenshots
![kern-4 screenshot-logo](https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/screenshot-logo.png)
*kern-4 splash screen*
<br/>
<br/>
![kern-4 screenshot-1](https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/screenshot-1.png)
*kern-4 interface along with the Pybullet training window (Dark Mode)*
<br/>
<br/>
![kern-4 screenshot-2](https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/screenshot-2.png)
*kern-4 interface (Gray & Ochre theme)*
