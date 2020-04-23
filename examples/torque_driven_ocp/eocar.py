import biorbd

from biorbd_optim import OptimalControlProgram
from biorbd_optim.problem_type import ProblemType
from biorbd_optim.objective_functions import ObjectiveFunction
from biorbd_optim.constraints import Constraint
from biorbd_optim.path_conditions import Bounds, QAndQDotBounds, InitialConditions
from biorbd_optim.plot import ShowResult


def prepare_ocp(biorbd_model_path="eocar.bioMod", show_online_optim=False):
    # --- Options --- #
    # Model path
    biorbd_model = biorbd.Model(biorbd_model_path)

    # Problem parameters
    number_shooting_points = 30
    final_time = 2
    torque_min, torque_max, torque_init = -100, 100, 0

    # Add objective functions
    objective_functions = {"type": ObjectiveFunction.minimize_torque, "weight": 100}

    # Dynamics
    problem_type = ProblemType.torque_driven

    # Constraints
    constraints = (
        {
            "type": Constraint.Type.MARKERS_TO_MATCH,
            "instant": Constraint.Instant.START,
            "first_marker": 0,
            "second_marker": 1,
        },
        {
            "type": Constraint.Type.MARKERS_TO_MATCH,
            "instant": Constraint.Instant.END,
            "first_marker": 0,
            "second_marker": 2,
        },
    )

    # Path constraint
    X_bounds = QAndQDotBounds(biorbd_model)

    for i in range(1, 6):
        X_bounds.first_node_min[i] = 0
        X_bounds.last_node_min[i] = 0
        X_bounds.first_node_max[i] = 0
        X_bounds.last_node_max[i] = 0
    X_bounds.last_node_min[2] = 1.57
    X_bounds.last_node_max[2] = 1.57

    # Initial guess
    X_init = InitialConditions([0] * (biorbd_model.nbQ() + biorbd_model.nbQdot()))

    # Define control path constraint
    U_bounds = Bounds(
        [torque_min] * biorbd_model.nbGeneralizedTorque(), [torque_max] * biorbd_model.nbGeneralizedTorque(),
    )
    U_init = InitialConditions([torque_init] * biorbd_model.nbGeneralizedTorque())

    # ------------- #

    return OptimalControlProgram(
        biorbd_model,
        problem_type,
        number_shooting_points,
        final_time,
        objective_functions,
        X_init,
        U_init,
        X_bounds,
        U_bounds,
        constraints,
        show_online_optim=show_online_optim,
    )


if __name__ == "__main__":
    ocp = prepare_ocp()

    # --- Solve the program --- #
    sol = ocp.solve()

    # --- Show results --- #
    result = ShowResult(ocp, sol)
    result.animate()