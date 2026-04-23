# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Location of the DUT
VERILOG_SOURCES = $(PWD)/arbiter.sv

# COCOTB_TOPLEVEL is the name of the toplevel module
COCOTB_TOPLEVEL = arbiter

# COCOTB_TEST_MODULES is the basename of the Python test file
COCOTB_TEST_MODULES = test_arbiter

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim