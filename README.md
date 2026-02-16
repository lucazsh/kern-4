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


<p align="right">
<img src="https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/robot.png" height="400">
</p>

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

![kern-4 screenshot-1](https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/screenshot-1.png)
*kern-4 interface along with the Pybullet training window (Dark Mode)*

![kern-4 screenshot-2](https://raw.githubusercontent.com/lucazsh/kern-4/main/3D%20models/img/screenshot-2.png)
*kern-4 interface (Gray & Ochre theme)*




























