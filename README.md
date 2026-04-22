# Blocks
Collection of useful RTL blocks and their TBs.

## Repository structure

Each folder contains RTL, TB and Makefile to run the tests. Finally the waveforms can be checked using GTKWave.

## Verification flow

- Activate cocotb
- Run "make" to execute the Makefile. This will put the DUTs go through tests
- Run "make WAVES=1" to execute the Makefile and generate waveform data
- Look at the waveforms by executing "gtkwave sim_build/fifo.fst". Add relevant signals in the GUI and click "Zoom to fit"
