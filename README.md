# Blocks

Collection of RTL blocks and their TBs.

## Repository structure

Each folder contains RTL, TB and Makefile to run the tests. [Icarus Verilog](https://steveicarus.github.io/iverilog/) is used as the simulation tool. Finally the waveforms can be checked using GTKWave.

Example of `a DUT passing all tests`:

![FIFO make](Images/fifo_make.png)

Example of `waveforms in GTKWave`:

![FIFO waveforms](Images/fifo_wf.png)

## Commands

- Navigate to the right place
- Activate **cocotb** for example: `source ~/venvs/cocotb/bin/activate`
  
```sh
make                             # Execute the Makefile
make WAVES=1                     # Execute the Makefile and generate waveform data
gtkwave sim_build/<NAME>.fst     # Open the waveform in GTKWave GUI
```

- Add relevant signals in the GUI and click "Zoom to fit"
