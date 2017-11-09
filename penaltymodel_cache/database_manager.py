import sqlite3

# from penaltymodel.serialization import serialize_graph, serialize_configurations, serialize_decision_variables

from penaltymodel_cache.schema import schema_statements
from penaltymodel_cache.cache_manager import cache_file


def cache_connect(database=None, directory=None):
    """TODO"""

    conn = sqlite3.connect(cache_file(database, directory))

    # let us go ahead and populate the database with the tables we need. Each table
    # is only created if it does not already exist
    with conn as cur:
        for statement in schema_statements:
            cur.execute(statement)

        # turn on foreign keys, allows deletes to cascade. That is if the graph
        # associated with a penaltymodel is removed, the penaltymodel will also
        # be removed. Also enforces that the graph exist when inserting.
        cur.execute("PRAGMA foreign_keys = ON;")

    return conn


def penalty_model_id(conn, penalty_model):
    """Returns the unique id associated with the given penalty model.

    If the penalty model is not currently in the cache, it is added
    and a new id is assigned. Thus, this function serves as the loading
    function for the cache.

    Args:
        conn (:obj:`sqlite3.Connection`): A connection to the cache.
        penalty_model (:obj:`penaltymodel.PenaltyModel`): The penalty
            model that the user wishes to determine the unique id for.

    Returns:
        int: The id associated with `penalty_model`.

    """

    penalty_model_dict = penalty_model.serialize()

    select = \
        """SELECT id from penalty_model_view WHERE
            num_nodes = :num_nodes AND
            num_edges = :num_edges AND
            edges = :edges AND
            num_variables = :num_variables AND
            num_feasible_configurations = :num_feasible_configurations AND
            feasible_configurations = :feasible_configurations AND
            energies = :energies AND
            linear_biases = :linear_biases AND
            quadratic_biases = :quadratic_biases AND
            offset = :offset AND
            decision_variables = :decision_variables AND
            classical_gap = :classical_gap AND
            ground_energy = :ground_energy
        ;"""
    insert = \
        """INSERT INTO penalty_model(
            decision_variables,
            classical_gap,
            ground_energy,
            graph_id,
            feasible_configurations_id,
            ising_model_id)
        VALUES(
            :decision_variables,
            :classical_gap,
            :ground_energy,
            :graph_id,
            :feasible_configurations_id,
            :ising_model_id);
        """

    with conn as cur:
        row = cur.execute(select, penalty_model_dict).fetchone()

        if row is None:
            # penalty model not found, so we're doing an insert

            # add the graph_id to penalty_model_dict
            _graph_id(cur, penalty_model_dict)

            # add the feasible_configurations_id to penalty_model_dict
            _feasible_configurations_id(cur, penalty_model_dict)

            # and finally add the ising_model_id to penalty_model_dict
            _ising_model_id(cur, penalty_model_dict)

            # alright, all the pieces should be there for an insert on penalty_model
            cur.execute(insert, penalty_model_dict)
            row = cur.execute(select, penalty_model_dict).fetchone()

    idx, = row
    return idx


def _graph_id(cur, penalty_model_dict):
    """Get the unique id associated with each graph in the cache. Updates the
    penalty_model_dict with graph_id field.

    Acts on the cursor. Intended use is to be invoked inside a with statement.
    """

    select = \
        """SELECT id from graph WHERE
            num_nodes = :num_nodes
            AND num_edges = :num_edges
            AND edges = :edges;
        """
    insert = \
        """INSERT INTO graph(num_nodes, num_edges, edges) VALUES
            (
                :num_nodes,
                :num_edges,
                :edges
            );
        """

    row = cur.execute(select, penalty_model_dict).fetchone()

    # if it's not there, insert and re-query
    if row is None:
        cur.execute(insert, penalty_model_dict)
        row = cur.execute(select, penalty_model_dict).fetchone()

    # None is not iterable so this is self checking
    penalty_model_dict['graph_id'], = row


def _feasible_configurations_id(cur, penalty_model_dict):
    """Get the unique id associated with the given feasible_configurations.
    Updates the penalty_model_dict with the feasible_configurations_id field.

    Acts on the cursor. Intended use is to be invoked inside a with statement.
    """

    select = """SELECT id FROM feasible_configurations WHERE
                    num_variables = :num_variables and
                    num_feasible_configurations = :num_feasible_configurations and
                    feasible_configurations = :feasible_configurations and
                    energies = :energies;
             """
    insert = """INSERT INTO feasible_configurations(
                    num_variables,
                    num_feasible_configurations,
                    feasible_configurations,
                    energies)
                VALUES (:num_variables, :num_feasible_configurations, :feasible_configurations, :energies);"""

    row = cur.execute(select, penalty_model_dict).fetchone()

    if row is None:
        cur.execute(insert, penalty_model_dict)
        row = cur.execute(select, penalty_model_dict).fetchone()

    # None is not iterable so this is self checking
    penalty_model_dict['feasible_configurations_id'], = row


def _ising_model_id(cur, penalty_model_dict):
    """Get the unique id associated with the given ising_model.
    Updates the penalty_model_dict with the ising_model_id field.

    Acts on the cursor. Intended use is to be invoked inside a with statement.
    """

    select = \
        """
        SELECT id from ising_model WHERE
            linear_biases = :linear_biases AND
            quadratic_biases = :quadratic_biases AND
            offset = :offset;
        """
    insert = \
        """
        INSERT INTO ising_model(
            linear_biases,
            quadratic_biases,
            offset,
            max_quadratic_bias,
            min_quadratic_bias,
            max_linear_bias,
            min_linear_bias)
        VALUES (
            :linear_biases,
            :quadratic_biases,
            :offset,
            :max_quadratic_bias,
            :min_quadratic_bias,
            :max_linear_bias,
            :min_linear_bias
            )
        """

    row = cur.execute(select, penalty_model_dict).fetchone()

    if row is None:
        cur.execute(insert, penalty_model_dict)
        row = cur.execute(select, penalty_model_dict).fetchone()

    # None is not iterable so this is self checking
    penalty_model_dict['ising_model_id'], = row
