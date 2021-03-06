"""
Run examples of PlanarSceneGraphVisualizer, e.g. to visualize a pendulum.
Usage demo: load a URDF, rig it up with a constant torque input, and draw it.
"""

import argparse

import numpy as np

from pydrake.common import FindResourceOrThrow
from pydrake.examples.manipulation_station import ManipulationStation
from pydrake.multibody.parsing import Parser
from pydrake.multibody.plant import AddMultibodyPlantSceneGraph
from pydrake.systems.analysis import Simulator
from pydrake.systems.framework import DiagramBuilder
from pydrake.systems.planar_scenegraph_visualizer import (
    PlanarSceneGraphVisualizer)


def run_pendulum_example(args):
    builder = DiagramBuilder()
    plant, scene_graph = AddMultibodyPlantSceneGraph(builder)
    parser = Parser(plant)
    parser.AddModelFromFile(FindResourceOrThrow(
        "drake/examples/pendulum/Pendulum.urdf"))
    plant.WeldFrames(plant.world_frame(), plant.GetFrameByName("base"))
    plant.Finalize()

    pose_bundle_output_port = scene_graph.get_pose_bundle_output_port()
    Tview = np.array([[1., 0., 0., 0.],
                      [0., 0., 1., 0.],
                      [0., 0., 0., 1.]],
                     dtype=np.float64)
    visualizer = builder.AddSystem(PlanarSceneGraphVisualizer(
        scene_graph, T_VW=Tview, xlim=[-1.2, 1.2], ylim=[-1.2, 1.2]))
    builder.Connect(pose_bundle_output_port, visualizer.get_input_port(0))

    diagram = builder.Build()
    simulator = Simulator(diagram)
    simulator.Initialize()
    simulator.set_target_realtime_rate(1.0)

    # Fix the input port to zero.
    plant_context = diagram.GetMutableSubsystemContext(
        plant, simulator.get_mutable_context())
    plant_context.FixInputPort(
        plant.get_actuation_input_port().get_index(),
        np.zeros(plant.num_actuators()))
    plant_context.SetContinuousState([0.5, 0.1])
    simulator.AdvanceTo(args.duration)


def run_manipulation_example(args):
    builder = DiagramBuilder()
    station = builder.AddSystem(ManipulationStation(time_step=0.005))
    station.SetupManipulationClassStation()
    station.Finalize()

    plant = station.get_multibody_plant()
    scene_graph = station.get_scene_graph()
    pose_bundle_output_port = station.GetOutputPort("pose_bundle")

    # Side-on view of the station.
    Tview = np.array([[1., 0., 0., 0.],
                      [0., 0., 1., 0.],
                      [0., 0., 0., 1.]],
                     dtype=np.float64)
    visualizer = builder.AddSystem(PlanarSceneGraphVisualizer(
        scene_graph, T_VW=Tview, xlim=[-0.5, 1.0], ylim=[-1.2, 1.2],
        draw_period=0.1))
    builder.Connect(pose_bundle_output_port, visualizer.get_input_port(0))

    diagram = builder.Build()
    simulator = Simulator(diagram)
    simulator.Initialize()
    simulator.set_target_realtime_rate(1.0)

    # Fix the control inputs to zero.
    station_context = diagram.GetMutableSubsystemContext(
        station, simulator.get_mutable_context())
    station.GetInputPort("iiwa_position").FixValue(
        station_context, station.GetIiwaPosition(station_context))
    station.GetInputPort("iiwa_feedforward_torque").FixValue(
        station_context, np.zeros(7))
    station.GetInputPort("wsg_position").FixValue(
        station_context, np.zeros(1))
    station.GetInputPort("wsg_force_limit").FixValue(
        station_context, [40.0])
    simulator.AdvanceTo(args.duration)


def main():
    np.set_printoptions(precision=5, suppress=True)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-T", "--duration",
                        type=float,
                        help="Duration to run sim in seconds.",
                        default=1.0)
    parser.add_argument("-m", "--models",
                        type=str,
                        nargs="*",
                        help="Models to run, at least one of [pend, manip]",
                        default=["pend"])
    args = parser.parse_args()

    for model in args.models:
        if model == "pend":
            run_pendulum_example(args)
        elif model == "manip":
            run_manipulation_example(args)
        else:
            print("Unrecognized model %s." % model)
            parser.print_usage()
            exit(1)


if __name__ == "__main__":
    main()
