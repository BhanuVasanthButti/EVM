

module evm #(parameter WIDTH = 7)(
    input  wire clk,
    input  wire rst,
    input  wire vote_candidate_1,
    input  wire vote_candidate_2,
    input  wire vote_candidate_3,
    input  wire switch_on_evm,         // Switch to turn ON the EVM
    input  wire candidate_ready,
    input  wire voting_session_done,
    input  wire [1:0] display_results,
    input  wire display_winner,
    output reg  [1:0] candidate_name,
    output reg  invalid_results,
    output reg  [WIDTH-1:0] results,
    output reg  voting_in_progress,
    output reg  voting_done
);

parameter IDLE                     = 3'b000, 
          WAITING_FOR_CANDIDATE    = 3'b001, 
          WAITING_FOR_CANDIDATE_TO_VOTE = 3'b010, 
          CANDIDATE_VOTED          = 3'b011, 
          VOTING_PROCESS_DONE      = 3'b100;

reg [WIDTH-1:0] candidate_1_vote_count, candidate_2_vote_count, candidate_3_vote_count;
reg [2:0] current_state, next_state;
reg vote_candidate_1_flag, vote_candidate_2_flag, vote_candidate_3_flag;



//---------------------------------------------
// Sequential logic
//---------------------------------------------
always @(posedge clk or negedge rst) begin
    if (!rst) begin
        current_state <= IDLE;
        candidate_1_vote_count <= {WIDTH{1'b0}};
        candidate_2_vote_count <= {WIDTH{1'b0}};
        candidate_3_vote_count <= {WIDTH{1'b0}};
        vote_candidate_1_flag <= 1'b0;
        vote_candidate_2_flag <= 1'b0;
        vote_candidate_3_flag <= 1'b0;
    end
    else if (!switch_on_evm) begin
        // Power-off/reset condition
        current_state <= IDLE;
        candidate_1_vote_count <= {WIDTH{1'b0}};
        candidate_2_vote_count <= {WIDTH{1'b0}};
        candidate_3_vote_count <= {WIDTH{1'b0}};
        vote_candidate_1_flag <= 1'b0;
        vote_candidate_2_flag <= 1'b0;
        vote_candidate_3_flag <= 1'b0;
    end
    else begin
        current_state <= next_state;
        case (current_state)
        
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
                if (vote_candidate_1 && !vote_candidate_2_flag && !vote_candidate_3_flag && !candidate_ready)
                    vote_candidate_1_flag <= 1'b1;
                else if (!vote_candidate_1_flag && vote_candidate_2 && !vote_candidate_3_flag && !candidate_ready)
                    vote_candidate_2_flag <= 1'b1;
                else if (!vote_candidate_1_flag && !vote_candidate_2_flag && vote_candidate_3 && !candidate_ready)
                    vote_candidate_3_flag <= 1'b1;
            end

            CANDIDATE_VOTED: begin
                if (vote_candidate_1_flag) begin
                    candidate_1_vote_count <= candidate_1_vote_count + 1;
                    vote_candidate_1_flag <= 1'b0;
                end
                else if (vote_candidate_2_flag) begin
                    candidate_2_vote_count <= candidate_2_vote_count + 1;
                    vote_candidate_2_flag <= 1'b0;
                end
                else if (vote_candidate_3_flag) begin
                    candidate_3_vote_count <= candidate_3_vote_count + 1;
                    vote_candidate_3_flag <= 1'b0;
                end
            end
            
            VOTING_PROCESS_DONE: begin
                  // Keep vote counts stable (do not modify them here).
                  // Clear any pending one-shot vote flags so returning to voting
                  // won't accidentally re-trigger counts.
                  vote_candidate_1_flag <= 1'b0;
                  vote_candidate_2_flag <= 1'b0;
                  vote_candidate_3_flag <= 1'b0;
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
end

//---------------------------------------------
// Combinational: Outputs
//---------------------------------------------
always @(*) begin
    candidate_name = 2'b00;
    invalid_results = 1'b0;
    voting_in_progress = 1'b0;
    voting_done = 1'b0;
    results = {WIDTH{1'b0}};

    case (current_state)
        IDLE: begin
            // Default cleared
            // All outputs remain at default values
            candidate_name = 2'b00;
            invalid_results = 1'b0;
            voting_in_progress = 1'b0;
            voting_done = 1'b0;
            results = {WIDTH{1'b0}};
        end

        WAITING_FOR_CANDIDATE_TO_VOTE: begin
            voting_in_progress = 1'b1;
        end

        CANDIDATE_VOTED: begin
            //voting_done = 1'b1;
        end

        VOTING_PROCESS_DONE: begin
            voting_done = 1'b1;
           if (   // Case 1: All three have equal votes
       ((candidate_1_vote_count == candidate_2_vote_count) &&
        (candidate_1_vote_count == candidate_3_vote_count) &&
        (candidate_2_vote_count == candidate_3_vote_count))
    || // Case 2: Candidate 1 & 2 tie for highest votes
       ((candidate_1_vote_count == candidate_2_vote_count) &&
        (candidate_1_vote_count > candidate_3_vote_count))
    || // Case 3: Candidate 1 & 3 tie for highest votes
       ((candidate_1_vote_count == candidate_3_vote_count) &&
        (candidate_1_vote_count > candidate_2_vote_count))
    || // Case 4: Candidate 2 & 3 tie for highest votes
       ((candidate_2_vote_count == candidate_3_vote_count) &&
        (candidate_2_vote_count > candidate_1_vote_count))
   ) begin
                invalid_results = 1'b1;
                
            end
            else begin
                invalid_results = 1'b0;
                if (display_winner) begin
                    if ((candidate_1_vote_count > candidate_2_vote_count) && (candidate_1_vote_count > candidate_3_vote_count)) begin
                        candidate_name = 2'b01;
                        results = candidate_1_vote_count;
                    end
                    else if ((candidate_2_vote_count > candidate_1_vote_count) && (candidate_2_vote_count > candidate_3_vote_count)) begin
                        candidate_name = 2'b10;
                        results = candidate_2_vote_count;
                    end
                    else begin
                        candidate_name = 2'b11;
                        results = candidate_3_vote_count;
                    end
                end
                else begin
                    case (display_results)
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

//---------------------------------------------
// Combinational: Next-state logic
//---------------------------------------------
always @(*) begin
    next_state = current_state;
    
    case (current_state)
        IDLE: begin
            if (switch_on_evm)
                next_state = WAITING_FOR_CANDIDATE;
            else
                next_state = IDLE;
        end

        WAITING_FOR_CANDIDATE: begin
            if (candidate_ready)
                next_state = WAITING_FOR_CANDIDATE_TO_VOTE;
            else if (voting_session_done)
                next_state = VOTING_PROCESS_DONE;
        end

        WAITING_FOR_CANDIDATE_TO_VOTE: begin
            if ((vote_candidate_1 && !vote_candidate_2_flag && !vote_candidate_3_flag && !candidate_ready) ||
                (!vote_candidate_1_flag && vote_candidate_2 && !vote_candidate_3_flag && !candidate_ready) ||
                (!vote_candidate_1_flag && !vote_candidate_2_flag && vote_candidate_3 && !candidate_ready) ||
                (vote_candidate_1_flag || vote_candidate_2_flag || vote_candidate_3_flag))
                next_state = CANDIDATE_VOTED;
        end

        CANDIDATE_VOTED: begin
            if (candidate_ready)
                next_state = WAITING_FOR_CANDIDATE_TO_VOTE;
            else
                next_state = WAITING_FOR_CANDIDATE;
        end

        VOTING_PROCESS_DONE: begin
            if (!switch_on_evm)
                next_state = IDLE;
            else
                next_state = VOTING_PROCESS_DONE;
        end

        default: next_state = IDLE;
    endcase
end

endmodule
