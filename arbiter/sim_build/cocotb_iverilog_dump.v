module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/arbiter.fst");
    $dumpvars(0, arbiter);
end
endmodule
