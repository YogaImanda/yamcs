# File: PS6_HOP_DHS_003.py
from yamcs import Procedure, prompt

# Stub fungsi helper


def procedure_initialize(apType, procName, ARGS):
    return {}


def mainStepFlowControl(stepId, stepName, g):
    pass


def stepFlowControl(stepId, stepName, g):
    pass


def cleanup(procName):
    pass

# ------------------------------------------------------------------------
# Main Procedure
# ------------------------------------------------------------------------


def run(proc: Procedure, apType="SHIP", ARGS=None):
    proc.step("INIT", "Initialization")
    g = procedure_initialize(apType, "PS6_HOP_DHS_003", ARGS)

    proc.step("START", "Begin EEPROM Readout and Comparison")
    mainStepFlowControl("START", "Begin EEPROM Readout and Comparison", g)

    # TODO: tambahkan logika actual readout EEPROM & compare dengan ground image
    prompt.ok("Performing EEPROM Readout and Comparison... (placeholder)")

    proc.step("999", "END")
    mainStepFlowControl("999", "END", g)
    cleanup("PS6_HOP_DHS_003")

    proc.step("END", "End PS6_HOP_DHS_003")
