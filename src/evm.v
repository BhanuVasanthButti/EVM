
module evm #(parameter WIDTH = 7)(
    input wire clk,
    input wire rst,
    input wire vote_candidate_1,    //Push Button - 1 
    input wire vote_candidate_2,    //Push Button - 2
    input wire vote_candidate_3,    //Push Button - 3
    input wire switch_on_evm,   //Switch to turn on the EVM from IDLE and wait for the candidate
    input wire candidate_ready, //Switch to indicate the candidate is ready to vote
    input wire voting_session_done,
    input wire [1:0] display_results,    //Switches to display the vote count of all the candidates
    input wire display_winner,  //Switch to display the winner
    //input wire switch_off_evm,
    output reg [1:0] candidate_name,
    output reg invalid_results,
    output reg [WIDTH-1:0] results,
    output reg voting_in_progress,  //LED indicating the candidate has entered the ballot and is yet to vote
    output reg voting_done  //LED indicating the candidate has voted and exited the poll
);

parameter IDLE = 3'b000, 
          WAITING_FOR_CANDIDATE = 3'b001, 
          WAITING_FOR_CANDIDATE_TO_VOTE = 3'b010, 
          CANDIDATE_VOTED = 3'b011, 
          VOTING_PROCESS_DONE = 3'b100;

reg [WIDTH-1:0] candidate_1_vote_count, candidate_2_vote_count, candidate_3_vote_count;
reg [2:0] current_state, next_state;
reg vote_candidate_1_flag, vote_candidate_2_flag, vote_candidate_3_flag;

// Sequential block: All registers and state updates
always@(posedge clk or negedge rst) begin
    if(!rst) begin
        // Reset all sequential elements
        current_state <= IDLE;
        candidate_1_vote_count <= {WIDTH{1'b0}};
        candidate_2_vote_count <= {WIDTH{1'b0}};
        candidate_3_vote_count <= {WIDTH{1'b0}};
        vote_candidate_1_flag <= 1'b0;
        vote_candidate_2_flag <= 1'b0;
        vote_candidate_3_flag <= 1'b0;
    end
    else begin
        // Update state
        current_state <= next_state;
        
        // Handle vote counting and flag management based on current state
        case(current_state)
            IDLE: begin
                // Clear all counters and flags when entering IDLE
                if(next_state == WAITING_FOR_CANDIDATE) begin
                    candidate_1_vote_count <= {WIDTH{1'b0}};
                    candidate_2_vote_count <= {WIDTH{1'b0}};
                    candidate_3_vote_count <= {WIDTH{1'b0}};
                    vote_candidate_1_flag <= 1'b0;
                    vote_candidate_2_flag <= 1'b0;
                    vote_candidate_3_flag <= 1'b0;
                end
            end
            
            WAITING_FOR_CANDIDATE_TO_VOTE: begin
                // Set vote flags when buttons are pressed (same logic as original)
                if(vote_candidate_1 && !vote_candidate_2_flag && !vote_candidate_3_flag && !candidate_ready) begin
                    vote_candidate_1_flag <= 1'b1;
                end
                else if(!vote_candidate_1_flag && vote_candidate_2 && !vote_candidate_3_flag && !candidate_ready) begin
                    vote_candidate_2_flag <= 1'b1;
                end
                else if(!vote_candidate_1_flag && !vote_candidate_2_flag && vote_candidate_3 && !candidate_ready) begin
                    vote_candidate_3_flag <= 1'b1;
                end
            end
            
            CANDIDATE_VOTED: begin
                // Process votes and clear flags (same logic as original)
                if(vote_candidate_1_flag) begin
                    candidate_1_vote_count <= candidate_1_vote_count + 1;
                    vote_candidate_1_flag <= 1'b0;
                end
                else if(vote_candidate_2_flag) begin
                    candidate_2_vote_count <= candidate_2_vote_count + 1;
                    vote_candidate_2_flag <= 1'b0;
                end
                else if(vote_candidate_3_flag) begin
                    candidate_3_vote_count <= candidate_3_vote_count + 1;
                    vote_candidate_3_flag <= 1'b0;
                end
                else begin
                    // Clear all flags as fallback
                    vote_candidate_1_flag <= 1'b0;
                    vote_candidate_2_flag <= 1'b0;
                    vote_candidate_3_flag <= 1'b0;
                end
            end
            
            default: begin
          /*  candidate_1_vote_count <= candidate_1_vote_count;
            candidate_2_vote_count <= candidate_2_vote_count;
            candidate_3_vote_count <= candidate_3_vote_count;
            vote_candidate_1_flag <= vote_candidate_1_flag;
            vote_candidate_2_flag <= vote_candidate_2_flag;
            vote_candidate_3_flag <= vote_candidate_3_flag; */ // Maintain current values in other states
            end
        endcase
    end
end

// Combinational block: Output assignments only
always@(*) begin
    // Default output assignments (prevents latches)
    candidate_name = 2'b00;
    invalid_results = 1'b0;
    voting_in_progress = 1'b0;
    voting_done = 1'b0;
    results = {WIDTH{1'b0}};
    
    case(current_state)
        IDLE: begin
            // All outputs remain at default values
            candidate_name = 2'b00;
            invalid_results = 1'b0;
            voting_in_progress = 1'b0;
            voting_done = 1'b0;
            results = {WIDTH{1'b0}};
        end
        WAITING_FOR_CANDIDATE: begin
            // All outputs remain at default values
            candidate_name = 2'b00;
            invalid_results = 1'b0;
            voting_in_progress = 1'b0;
            voting_done = 1'b0;
            results = {WIDTH{1'b0}};
        end
        WAITING_FOR_CANDIDATE_TO_VOTE: begin
            candidate_name = 2'b00;
            invalid_results = 1'b0;
            voting_in_progress = 1'b1;        // Only this differs from default
            voting_done = 1'b0;
            results = {WIDTH{1'b0}};
        end
        CANDIDATE_VOTED: begin
            candidate_name = 2'b00;
            invalid_results = 1'b0;
            voting_in_progress = 1'b0;
            voting_done = 1'b1;               // Only this differs from default
            results = {WIDTH{1'b0}};
        end
        VOTING_PROCESS_DONE: begin
            // Check for tie conditions
            if((candidate_1_vote_count == candidate_2_vote_count) || 
               (candidate_1_vote_count == candidate_3_vote_count) ||
               (candidate_2_vote_count == candidate_3_vote_count)) begin
                invalid_results = 1'b1;
            end    
            else begin
                invalid_results = 1'b0;
                if(display_winner) begin
                    if((candidate_1_vote_count > candidate_2_vote_count) && (candidate_1_vote_count > candidate_3_vote_count)) begin
                        candidate_name = 2'b01;
                        results = candidate_1_vote_count;
                    end
                    else if((candidate_2_vote_count > candidate_1_vote_count) && (candidate_2_vote_count > candidate_3_vote_count)) begin
                        candidate_name = 2'b10;
                        results = candidate_2_vote_count;
                    end
                    else begin
                        candidate_name = 2'b11;
                        results = candidate_3_vote_count;
                    end
                end
                else begin       
                    case(display_results)
                        2'b00: begin results = candidate_1_vote_count; candidate_name = 2'b01; end
                        2'b01: begin results = candidate_2_vote_count; candidate_name = 2'b10; end
                        2'b10: begin results = candidate_3_vote_count; candidate_name = 2'b11; end
                        default: begin results = {WIDTH{1'b0}}; candidate_name = 2'b00; end
                    endcase
                end
            end
        end
        default: begin
            /*candidate_1_vote_count <= candidate_1_vote_count;
            candidate_2_vote_count <= candidate_2_vote_count;
            candidate_3_vote_count <= candidate_3_vote_count;
            vote_candidate_1_flag <= vote_candidate_1_flag;
            vote_candidate_2_flag <= vote_candidate_2_flag;
            vote_candidate_3_flag <= vote_candidate_3_flag;*/
        end
    endcase
end

// Combinational block: Next state logic only
always@(*) begin
    // Default assignment prevents latches
    next_state = current_state;
    
    case(current_state)
        IDLE: begin
            if(switch_on_evm)
                next_state = WAITING_FOR_CANDIDATE;
            else
                next_state = IDLE;
        end
        WAITING_FOR_CANDIDATE: begin
            if(candidate_ready)
                next_state = WAITING_FOR_CANDIDATE_TO_VOTE;
            else if(voting_session_done)
                next_state = VOTING_PROCESS_DONE;
            else
                next_state = WAITING_FOR_CANDIDATE;
        end
        WAITING_FOR_CANDIDATE_TO_VOTE: begin
            // Transition to CANDIDATE_VOTED when any flag is set
            if((vote_candidate_1 && !vote_candidate_2_flag && !vote_candidate_3_flag && !candidate_ready) ||
               (!vote_candidate_1_flag && vote_candidate_2 && !vote_candidate_3_flag && !candidate_ready) ||
               (!vote_candidate_1_flag && !vote_candidate_2_flag && vote_candidate_3 && !candidate_ready) ||
               (vote_candidate_1_flag || vote_candidate_2_flag || vote_candidate_3_flag)) begin
                next_state = CANDIDATE_VOTED;
            end
            else
                next_state = WAITING_FOR_CANDIDATE_TO_VOTE;
        end
        CANDIDATE_VOTED: begin
            if(candidate_ready)
                next_state = WAITING_FOR_CANDIDATE_TO_VOTE;
            else
                next_state = WAITING_FOR_CANDIDATE;
        end
        VOTING_PROCESS_DONE: begin
            if(!switch_on_evm)
                next_state = IDLE;
            else
                next_state = VOTING_PROCESS_DONE;
        end
        default: begin
            next_state = IDLE;
        end    
    endcase
end

endmodule
