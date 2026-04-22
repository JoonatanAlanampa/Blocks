module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/fifo.fst");
    $dumpvars(0, fifo);
end
endmodule
