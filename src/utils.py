import sys
import traceback


def print_stack():
    """
    catch stack after exception
    """
    # cath exception with sys and return the error stack
    ex_type, ex_value, ex_traceback = sys.exc_info()
    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(ex_traceback)
    # Format stacktrace
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append(
            "File : %s , Line : %d, Func.Name : %s, Message : %s"
            % (trace[0], trace[1], trace[2], trace[3])
        )
    error = ex_type.__name__ + "\n" + str(ex_value) + "\n"
    for err in stack_trace:
        error = error + str(err) + "\n"

    return error
