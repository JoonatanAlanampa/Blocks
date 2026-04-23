module arbiter (
    input logic         clk,
    input logic         rst_n,

    // Channel 0
    input logic         in0_valid,
    input logic [7:0]   in0_data,
    output logic        in0_ready,

    // Channel 1
    input logic         in1_valid,
    input logic [7:0]   in1_data,
    output logic        in1_ready,

    // Output channel
    output logic        out_valid,
    output logic [7:0]  out_data,
    output logic        out_src, // 0 = ch0, 1 = ch1
    input  logic        out_ready
);

    // Round-robin priority: 0=ch0 has priority next, 1=ch1 has priority next
    logic       grant_q;

    // One-entry holding register for backpressure
    logic       hold_valid_q;
    logic [7:0] hold_data_q;
    logic       hold_src_q;
    logic       hold_contended_q; // 1 if both inputs were valid when item was chosen

    // Current combinational selection
    logic       sel_valid_c;
    logic [7:0] sel_data_c;
    logic       sel_src_c;
    logic       contended_c;

    // Choose winner when not holding
    always_comb begin

        sel_valid_c = 1'b0;
        sel_data_c  = 8'd0;
        sel_src_c   = 1'b0;
        contended_c = 1'b0;

        // Only channel 0 valid
        if (in0_valid && !in1_valid) begin
            sel_valid_c = 1'b1;
            sel_data_c  = in0_data;
            sel_src_c   = 1'b0;
        end
        // Only channel 1 valid
        else if (!in0_valid && in1_valid) begin
            sel_valid_c = 1'b1;
            sel_data_c  = in1_data;
            sel_src_c   = 1'b1;
        end
        // Both valid
        else if (in0_valid && in1_valid) begin
            sel_valid_c = 1'b1;
            contended_c = 1'b1;

            if (grant_q == 1'b0) begin
                sel_data_c  = in0_data;
                sel_src_c   = 1'b0;
            end
            else begin
                sel_data_c  = in1_data;
                sel_src_c   = 1'b1;
            end
        end
    end

    // Output side and upstream ready signals
    always_comb begin

        out_valid   = 1'b0;
        out_data    = 8'd0;
        out_src     = 1'b0;
        in0_ready   = 1'b0;
        in1_ready   = 1'b0;

        if (hold_valid_q) begin
            // Hold output stable during backpressure
            out_valid   = 1'b1;
            out_data    = hold_data_q;
            out_src     = hold_src_q;
        end
        else begin
            out_valid   = sel_valid_c;
            out_data    = sel_data_c;
            out_src     = sel_src_c;

            // One-entry internal buffer:
            // if we are not already holding something, we can accept the selected input
            if (sel_valid_c) begin
                if (sel_src_c == 1'b0) begin
                    in0_ready = 1'b1;
                end else begin
                    in1_ready = 1'b1;
                end
            end
        end
    end

    // State update, hold and round-robin priority
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant_q          <= 1'b0; // ch0 gets first priority after reset
            hold_valid_q     <= 1'b0;
            hold_data_q      <= 8'd0;
            hold_src_q       <= 1'b0;
            hold_contended_q <= 1'b0;
        end
        else begin
            // Currently holding a stalled output item
            if (hold_valid_q) begin
                if (out_ready) begin
                    hold_valid_q <= 1'b0;

                    // Toggle RR priority only if this item was chosen under contention
                    if (hold_contended_q) begin
                        grant_q <= ~hold_src_q;
                    end
                end
            end
            else begin
                // Not holding: maybe accept a newly selected item
                if (sel_valid_c) begin
                    if (out_ready) begin
                        // Immediate transfer to downstream this cycle
                        if (contended_c) begin
                            grant_q <= ~sel_src_c;
                        end
                    end
                    else begin
                        // Downstream stalled: capture selected item and hold it
                        hold_valid_q     <= 1'b1;
                        hold_data_q      <= sel_data_c;
                        hold_src_q       <= sel_src_c;
                        hold_contended_q <= contended_c;
                    end
                end
            end
        end
    end

endmodule