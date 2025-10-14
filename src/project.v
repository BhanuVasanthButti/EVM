/*

* Copyright (c) 2024 Your Name

* SPDX-License-Identifier: Apache-2.0

*/
 
`default_nettype none
 
module tt_um_evm (

    input  wire [7:0] ui_in,    // Dedicated inputs

    output wire [7:0] uo_out,   // Dedicated outputs

    input  wire [7:0] uio_in,   // IOs: Input path

    output wire [7:0] uio_out,  // IOs: Output path

    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)

    input  wire       ena,      // always 1 when the design is powered, so you can ignore it

    input  wire       clk,      // clock

    input  wire       rst_n     // reset_n - low to reset

);
 
  // All output pins must be assigned. If not used, assign to 0.

  //assign uo_out  = ui_in + uio_in;  // Example: ou_out is the sum of ui_in and uio_in

    assign uio_out[7] = 0;

    assign uo_out[5] = 0;

    assign uo_out[6] = 0;

    assign uo_out[7] = 0;

    assign uio_oe  = 0;
 
    evm dut(

        .clk(clk),

        .rst(rst_n),

        .vote_candidate_1(ui_in[0]),

        .vote_candidate_2(ui_in[1]),

        .vote_candidate_3(ui_in[2]),

        .switch_on_evm(ui_in[3]),

        .candidate_ready(ui_in[4]),

        .voting_session_done(ui_in[5]),

       // .switch_off_evm(ui_in[6]),

        .display_winner(ui_in[7]),

        .display_results(uio_in[1:0]),

        .candidate_name(uo_out[1:0]),

        .invalid_results(uo_out[2]),

        .results(uio_out[6:0]),

        .voting_in_progress(uo_out[3]),

        .voting_done(uo_out[4])

    );  
 
  // List all unused inputs to prevent warnings

 wire _unused = &{ui_in[6],ena, uio_in[7:2], 1'b0};
 
endmodule
 
