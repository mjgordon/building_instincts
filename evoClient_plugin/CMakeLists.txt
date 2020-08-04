cmake_minimum_required(VERSION 3.16)
project(evoClient_plugin)

set(CMAKE_CXX_STANDARD 14)

include_directories(/home/mrac/CoppeliaSim_Edu_V4_1_0_Ubuntu18_04/programming/include)
include_directories(/home/mrac/ros_workspace/src/ros_brain/include/MultiNEAT)
include_directories(/usr/include/python2.7)

add_library(simExtEVO2 SHARED
        src/simLib.h
        src/simLib.cpp
        src/EvoClientPluginTools.h
        src/EvoClientPluginTools.cpp
        src/simExtEVO2.h
        src/simExtEVO2.cpp
)

target_link_libraries(simExtEVO2
        python2.7
        MultiNEAT)
#        /home/mrac/CoppeliaSim_Edu_V4_0_0_Ubuntu18_04/libboost_python-py27.so.1.54.0
#        /home/mrac/CoppeliaSim_Edu_V4_0_0_Ubuntu18_04/libboost_serialization.so.1.54.0)

