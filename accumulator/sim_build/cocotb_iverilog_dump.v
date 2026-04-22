module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/accumulator.fst");
    $dumpvars(0, accumulator);
end
endmodule
