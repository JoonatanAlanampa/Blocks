module accumulator (
    input  logic clk,
    input  logic rst_n,
    input  logic clear,
    input  logic load_en,
    input  logic add_en,
    input  logic [7:0] load_data,
    input  logic [7:0] add_data,
    output logic [7:0] sum,
    output logic overflow
);

    logic [8:0] tmp_sum;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum <= '0;
            overflow <= '0;
        end 
        else begin
            overflow <= '0;
            if (clear) begin
                sum <= '0;
            end
            else if (load_en) begin
                sum <= load_data;
            end
            else if (add_en) begin
                tmp_sum = sum + add_data;
                sum <= tmp_sum[7:0];
                overflow <= tmp_sum[8];
            end
        end
    end

endmodule