module fifo (
    input   logic           clk,
    input   logic           rst_n,
    input   logic           wr_en,
    input   logic           rd_en,
    input   logic    [7:0]  wdata,
    output  logic    [7:0]  rdata,
    output  logic           full,
    output  logic           empty,
    output  logic    [2:0]  count
);

    logic [7:0] mem [0:3];
    logic [1:0] wr_ptr, rd_ptr;

    assign empty    = (count == 3'd0);
    assign full     = (count == 3'd4);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count   <= 3'd0;
            wr_ptr  <= 2'd0;
            rd_ptr  <= 2'd0;
            rdata   <= 8'd0;
        end
        else begin
            // Write only
            if (wr_en && !full && !rd_en) begin
                mem[wr_ptr] <= wdata;
                wr_ptr      <= wr_ptr + 2'd1;
                count       <= count + 3'd1;
            end
            // Read only
            else if (rd_en && !empty && !wr_en) begin
                rdata   <= mem[rd_ptr];
                rd_ptr  <= rd_ptr + 2'd1;
                count   <= count - 3'd1;
            end
            // Write and read: both happen
            else if (wr_en && rd_en && !full && !empty) begin
                mem[wr_ptr] <= wdata;
                wr_ptr      <= wr_ptr + 2'd1;
                rdata       <= mem[rd_ptr];
                rd_ptr      <= rd_ptr + 2'd1;
            end
            // Write and read: write only
            else if (wr_en && rd_en && empty) begin
                mem[wr_ptr] <= wdata;
                wr_ptr      <= wr_ptr + 2'd1;
                count       <= count + 3'd1;
            end
            // Write and read: read only
            else if (wr_en && rd_en && full) begin
                rdata   <= mem[rd_ptr];
                rd_ptr  <= rd_ptr + 2'd1;
                count   <= count - 3'd1;
            end
        end
    end

endmodule