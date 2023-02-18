
import os
import pytest
import numpy as np
from casadi import MX, DM, vertcat, Function
import biorbd_casadi as biorbd
from bioptim import (
    MultiBiorbdModel,
    BiMappingList,
)


def test_biorbd_model_import():
    from bioptim.examples.torque_driven_ocp import example_multi_biorbd_model as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)
    biorbd_model_path = "/models/triple_pendulum.bioMod"
    biorbd_model_path_modified_inertia = "/models/triple_pendulum_modified_inertia.bioMod"
    MultiBiorbdModel((bioptim_folder + biorbd_model_path, bioptim_folder + biorbd_model_path_modified_inertia))

    MultiBiorbdModel((biorbd.Model(bioptim_folder + biorbd_model_path), biorbd.Model(bioptim_folder + biorbd_model_path_modified_inertia)))

    with pytest.raises(RuntimeError, match="Type must be a tuple"):
        MultiBiorbdModel(1)


# TODO: test all casses with models containing at least on element (muscles, contacts, ...)
def test_biorbd_model():
    from bioptim.examples.torque_driven_ocp import example_multi_biorbd_model as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)
    biorbd_model_path = "/models/triple_pendulum.bioMod"
    biorbd_model_path_modified_inertia = "/models/triple_pendulum_modified_inertia.bioMod"
    models = MultiBiorbdModel((bioptim_folder + biorbd_model_path, bioptim_folder + biorbd_model_path_modified_inertia))


    nb_q = models.nb_q
    nb_qdot = models.nb_qdot
    nb_qddot = models.nb_qddot
    nb_root = models.nb_root
    nb_tau = models.nb_tau
    nb_quaternions = models.nb_quaternions
    nb_segments = models.nb_segments
    nb_muscles = models.nb_muscles
    nb_soft_contacts = models.nb_soft_contacts
    nb_markers = models.nb_markers
    nb_rigid_contacts = models.nb_rigid_contacts
    nb_contacts = models.nb_contacts
    nb_dof = models.nb_dof

    name_dof = models.name_dof
    contact_names = models.contact_names
    soft_contact_names = models.soft_contact_names
    marker_names = models.marker_names
    muscle_names = models.muscle_names

    states_mapping = BiMappingList()
    states_mapping.add('q', [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5])
    states_mapping.add('qdot', [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5])
    states_mapping.add('qddot', [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5])
    states_mapping.add('tau', [None, 0, 1, None, 0, 2], [1, 2, 5])
    q_mapping = states_mapping['q']
    qdot_mapping = states_mapping['qdot']
    qddot_mapping = states_mapping['qddot']
    tau_mapping = states_mapping['tau']

    np.random.seed(42)
    q = MX(np.random.random((nb_q, )))
    qdot = MX(np.random.random((nb_qdot, )))
    tau = MX(np.random.random((nb_tau, )))
    qddot_joints = MX(np.random.random((nb_tau - nb_root, )))
    f_ext = MX(6)
    f_contact = MX(6)
    muscle_excitations = MX(np.random.random((nb_muscles, )))

    # model_deep_copied = models.deep_copy() # TODO: Fix deep copy
    models.copy()
    models.serialize()
    models.set_gravity(np.array([0, 0, -3]), 0)
    model_gravity_modified = Function("Gravity", [], [models.gravity])()["o0"]
    segment_index = models.segment_index("Seg1", 0)
    segments = models.segments
    homogeneous_matrices_in_global = Function("RT_parent", [], [models.homogeneous_matrices_in_global(q[:3], 0, 0).to_mx()])()["o0"]
    homogeneous_matrices_in_child = Function("RT_child", [], [models.homogeneous_matrices_in_child(0)[0].to_mx()])()["o0"]
    mass = Function("Mass", [], [models.mass])()["o0"]
    center_of_mass = Function("CoM", [], [models.center_of_mass(q)])()["o0"]
    center_of_mass_velocity = Function("CoMdot", [], [models.center_of_mass_velocity(q, qdot)])()["o0"]
    center_of_mass_acceleration = Function("CoMddot", [], [models.center_of_mass_acceleration(q, qdot, qdot)])()["o0"]
    angular_momentum = Function("AngMom", [], [models.angular_momentum(q, qdot)])()["o0"]
    reshape_qdot = Function("GetQdot", [], [models.reshape_qdot(q, qdot, 1)])()["o0"]
    segment_angular_velocity = Function("SegmentAngMom", [], [models.segment_angular_velocity(q, qdot, 0)])()["o0"]
    # soft_contact = Function("SoftContact", [], [models.soft_contact(0, 0)])()["o0"]  # TODO: Fix soft contact (biorbd call error)
    # torque = Function("TorqueFromActivation", [], [models.torque(tau, q, qdot)])()["o0"]  #TODO: Fix torque (Close the actuator model before calling torqueMax)
    forward_dynamics_free_floating_base = Function("RootForwardDynamics", [], [models.forward_dynamics_free_floating_base(q, qdot, qddot_joints)])()["o0"]
    forward_dynamics = Function("ForwardDynamics", [], [models.forward_dynamics(q, qdot, tau)])()["o0"]
    constrained_forward_dynamics = Function("ConstrainedForwardDynamics", [], [models.constrained_forward_dynamics(q, qdot, tau, f_ext)])()["o0"]
    inverse_dynamics = Function("InverseDynamics", [], [models.inverse_dynamics(q, qdot, tau)])()["o0"]
    contact_forces_from_constrained_dynamics = Function("ContactForcesFromDynamics", [], [models.contact_forces_from_constrained_forward_dynamics(q, qdot, tau, f_ext)])()["o0"]
    qdot_from_impact = Function("QdotFromImpact", [], [models.qdot_from_impact(q, qdot)])()["o0"]
    muscle_activation_dot = Function("MusActivationdot", [], [models.muscle_activation_dot(muscle_excitations)])()["o0"]
    muscle_joint_torque = Function("MusTau", [], [models.muscle_joint_torque(muscle_excitations, q, qdot)])()["o0"]
    markers = Function("Markers", [], [models.markers(q)[0]])()["o0"]
    marker = Function("Marker", [], [models.marker(q[:3], index=0, model_index=0, reference_segment_index=0)])()["o0"]
    marker_index = models.marker_index("marker_3", 0)
    marker_velocities = Function("Markerdot", [], [models.marker_velocities(q, qdot, reference_index=0)])()["o0"]
    tau_max = models.tau_max(q, qdot)
    # rigid_contact_acceleration = models.rigid_contact_acceleration(q, qdot, qddot, 0) # to be added when the code works
    soft_contact_forces = models.soft_contact_forces(q, qdot)
    reshape_fext_to_fcontact = models.reshape_fext_to_fcontact(f_ext)
    normalize_state_quaternions = models.normalize_state_quaternions(vertcat(q, qdot))
    get_quaternion_idx = models.get_quaternion_idx()
    contact_forces = models.contact_forces(q, qdot, tau, f_ext)
    passive_joint_torque = models.passive_joint_torque(q, qdot)
    q_mapping = models._q_mapping(q_mapping)
    qdot_mapping = models._q_mapping(qdot_mapping)
    qddot_mapping = models._q_mapping(qddot_mapping)
    tau_mapping = models._q_mapping(tau_mapping)
    bounds_from_ranges = models.bounds_from_ranges(['q', 'qdot'], states_mapping)

    np.testing.assert_equal(nb_q, 6)
    np.testing.assert_equal(nb_qdot, 6)
    np.testing.assert_equal(nb_qddot, 6)
    np.testing.assert_equal(nb_root, 1)
    np.testing.assert_equal(nb_tau, 6)
    np.testing.assert_equal(nb_quaternions, 0)
    np.testing.assert_equal(nb_segments, 6)
    np.testing.assert_equal(nb_muscles, 0)
    np.testing.assert_equal(nb_soft_contacts, 0)
    np.testing.assert_equal(nb_markers, 12)
    np.testing.assert_equal(nb_rigid_contacts, 0)
    np.testing.assert_equal(nb_contacts, 0)
    np.testing.assert_equal(nb_dof, 6)

    np.testing.assert_equal(name_dof, ('Seg1_RotX', 'Seg2_RotX', 'Seg3_RotX', 'Seg1_RotX', 'Seg2_RotX', 'Seg3_RotX'))
    np.testing.assert_equal(contact_names, ())
    np.testing.assert_equal(soft_contact_names, ())
    np.testing.assert_equal(marker_names, ('marker_1', 'marker_2', 'marker_3', 'marker_4', 'marker_5', 'marker_6', 'marker_1', 'marker_2', 'marker_3', 'marker_4', 'marker_5', 'marker_6'))
    np.testing.assert_equal(muscle_names, ())

    for i in range(model_gravity_modified.shape[0]):
        np.testing.assert_almost_equal(model_gravity_modified[i], DM(np.array([0, 0, -3, 0, 0, -9.81])[i]))

    np.testing.assert_equal(segment_index, 0)

    for i in range(homogeneous_matrices_in_global.shape[0]):
        for j in range(homogeneous_matrices_in_global.shape[1]):
            np.testing.assert_almost_equal(homogeneous_matrices_in_global[i, j], DM(np.array([[1, 0, 0, 0], [0, 0.930676, -0.365845, 0], [0, 0.365845, 0.930676, 0], [0, 0, 0, 1]])[i, j]), decimal=5)

    for i in range(homogeneous_matrices_in_child.shape[0]):
        for j in range(homogeneous_matrices_in_child.shape[1]):
            np.testing.assert_almost_equal(homogeneous_matrices_in_child[i, j], DM(np.eye(4)[i, j]))

    for i in range(mass.shape[0]):
        np.testing.assert_almost_equal(mass[i], DM(np.array([3, 3][i])))

    for i in range(center_of_mass.shape[0]):
        np.testing.assert_almost_equal(center_of_mass[i], DM(np.array([-0.0005, 1.28949, -0.875209, -0.0005, 1.30214, -1.43631])[i]), decimal=5)

    for i in range(center_of_mass_velocity.shape[0]):
        np.testing.assert_almost_equal(center_of_mass_velocity[i], DM(np.array([0, -0.0792032, 1.02386, 0, 1.20171, 1.19432])[i]), decimal=5)

    for i in range(center_of_mass_acceleration.shape[0]):
        np.testing.assert_almost_equal(center_of_mass_acceleration[i], DM(np.array([0, -1.2543, 0.750037, 0, -0.097267, 2.34977])[i]), decimal=5)

    for i in range(angular_momentum.shape[0]):
        np.testing.assert_almost_equal(angular_momentum[i],
                                       DM(np.array([2.09041, -2.1684e-19, -1.0842e-19, 2.41968, 2.1684e-19, -2.1684e-19])[i]), decimal=5)

    for i in range(reshape_qdot.shape[0]):
        np.testing.assert_almost_equal(reshape_qdot[i],
                                       DM(np.array([0.0580836, 0.866176, 0.601115, 0, 0, 0, 0.0580836, 0.866176, 0.601115, 0, 0, 0])[i]), decimal=5)

    for i in range(segment_angular_velocity.shape[0]):
        np.testing.assert_almost_equal(segment_angular_velocity[i], DM(np.array([0.92426, 0, 0, 0.728657, 0, 0])[i]), decimal=5)

    for i in range(forward_dynamics_free_floating_base.shape[0]):
        np.testing.assert_almost_equal(forward_dynamics_free_floating_base[i], DM(np.array([-1.07327, -3.15174])[i]), decimal=5)

    for i in range(forward_dynamics.shape[0]):
        np.testing.assert_almost_equal(forward_dynamics[i], DM(np.array([1.00257, -3.23703, 0.992444, -2.50109, -0.735689, 0.758181])[i]), decimal=5)

    for i in range(constrained_forward_dynamics.shape[0]):
        np.testing.assert_almost_equal(constrained_forward_dynamics[i], DM(np.array([1.00257, -3.23703, 0.992444, -2.50109, -0.735689, 0.758181])[i]), decimal=5)

    for i in range(inverse_dynamics.shape[0]):
        np.testing.assert_almost_equal(inverse_dynamics[i], DM(np.array([15.8644, 12.6384, 4.74421, 43.1401, 25.1079, 9.67661])[i]), decimal=5)

    for i in range(contact_forces_from_constrained_dynamics.shape[0]):
        np.testing.assert_almost_equal(contact_forces_from_constrained_dynamics[i], DM(np.array([1.00257, -3.23703, 0.992444, -2.50109, -0.735689, 0.758181])[i]), decimal=5)

    for i in range(qdot_from_impact.shape[0]):
        np.testing.assert_almost_equal(qdot_from_impact[i], DM(np.array([0.0580836, 0.866176, 0.601115, 0.708073, 0.0205845, 0.96991])[i]), decimal=5)

    np.testing.assert_equal(muscle_activation_dot.shape, (0, 1))

    for i in range(muscle_joint_torque.shape[0]):
        np.testing.assert_almost_equal(muscle_joint_torque[i], DM(np.zeros((6, ))[i]), decimal=5)

    for i in range(markers.shape[0]):
        np.testing.assert_almost_equal(markers[i], DM(np.zeros((3, ))[i]), decimal=5)

    for i in range(marker.shape[0]):
        np.testing.assert_almost_equal(marker[i], DM(np.zeros((3, ))[i]), decimal=5)

    np.testing.assert_equal(marker_index, 2)


