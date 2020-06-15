import biorbd
import pickle
from time import time
from casadi import vertcat

from biorbd_optim import (
    OptimalControlProgram,
    ProblemType,
    Problem,
    Dynamics,
    Bounds,
    QAndQDotBounds,
    InitialConditions,
    ShowResult,
    Objective,
)


def custom_dynamic(states, controls, parameters, nlp):
    Dynamics.apply_parameters(parameters, nlp)
    q, qdot, tau = Dynamics.dispatch_q_qdot_tau_data(states, controls, nlp)

    qdot_reduced = nlp["q_mapping"].reduce.map(qdot)
    qddot = biorbd.Model.ForwardDynamics(nlp["model"], q, qdot, tau).to_mx()
    qddot_reduced = nlp["q_dot_mapping"].reduce.map(qddot)

    return vertcat(qdot_reduced, qddot_reduced)


def custom_torque_driven(ocp, nlp):
    Problem.configure_q_qdot(nlp, True, False)
    Problem.configure_tau(nlp, False, True)
    Problem.configure_forward_dyn_func(ocp, nlp, custom_dynamic)


def prepare_ocp(biorbd_model_path, final_time, number_shooting_points, nb_threads):
    # --- Options --- #
    biorbd_model = biorbd.Model(biorbd_model_path)
    torque_min, torque_max, torque_init = -100, 100, 0
    n_q = biorbd_model.nbQ()
    n_qdot = biorbd_model.nbQdot()
    n_tau = biorbd_model.nbGeneralizedTorque()

    # Add objective functions
    objective_functions = {"type": Objective.Lagrange.MINIMIZE_TORQUE_DERIVATIVE}

    # Dynamics
    problem_type = {"type": ProblemType.CUSTOM, "function": custom_torque_driven}

    # Constraints
    constraints = ()

    # Path constraint
    X_bounds = QAndQDotBounds(biorbd_model)
    X_bounds.min[:, [0, -1]] = 0
    X_bounds.max[:, [0, -1]] = 0
    X_bounds.min[1, -1] = 3.14
    X_bounds.max[1, -1] = 3.14

    # Initial guess
    X_init = InitialConditions([0] * (n_q + n_qdot))

    # Define control path constraint
    U_bounds = Bounds(min_bound=[torque_min] * n_tau, max_bound=[torque_max] * n_tau)
    U_bounds.min[n_tau - 1, :] = 0
    U_bounds.max[n_tau - 1, :] = 0

    U_init = InitialConditions([torque_init] * n_tau)

    # ------------- #

    return OptimalControlProgram(
        biorbd_model,
        problem_type,
        number_shooting_points,
        final_time,
        X_init,
        U_init,
        X_bounds,
        U_bounds,
        objective_functions,
        constraints,
        nb_threads=nb_threads,
    )


if __name__ == "__main__":
    ocp = prepare_ocp(biorbd_model_path="pendulum.bioMod", final_time=3, number_shooting_points=100, nb_threads=4)

    # --- Solve the program --- #
    tic = time()
    sol, sol_iterations = ocp.solve(show_online_optim=True, return_iterations=True)
    toc = time() - tic
    print(f"Time to solve : {toc}sec")

    # --- Access to all iterations  --- #
    nb_iter = len(sol_iterations)
    third_iteration = sol_iterations[2]

    # --- Save result of get_data --- #
    ocp.save_get_data(sol, "pendulum.bob", sol_iterations)  # you don't have to specify the extension ".bob"

    # --- Load result of get_data --- #
    with open("pendulum.bob", "rb") as file:
        data = pickle.load(file)

    # --- Save the optimal control program and the solution --- #
    ocp.save(sol, "pendulum.bo")  # you don't have to specify the extension ".bo"

    # --- Load the optimal control program and the solution --- #
    ocp_load, sol_load = OptimalControlProgram.load("pendulum.bo")

    # --- Show results --- #
    result = ShowResult(ocp_load, sol_load)
    result.animate()
