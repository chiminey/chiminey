// Developed by Ahmed Abdullah,
// AICAUSE Lab, RMIT Universiy. November 2016

dtmc

const double rho;
const double sigma;
const double epsilon;
const double pi;
const double tau_1;
const double phi_1;
const double phi_0;
const double alpha;
const double theta;

module main
  s: [-1..5] init 0;

  [] s=-1 -> (s'=-1);
  [] s=0 -> sigma   : (s'=-1) + rho : (s'=1) + pi : (s'=2) + 1 - sigma - rho - pi: (s'=0);
  [] s=1 -> 1-epsilon : (s'=0) + epsilon  : (s'=5);
  [] s=2 -> phi_0: (s'=1) + tau_1: (s'=3) + phi_1: (s'=4) + 1 - phi_0 - tau_1 - phi_1: (s'=0);
  [] s=3 -> (alpha * theta): (s'=0) + 1 - (alpha * theta): (s'=1);
  [] s=4 -> (s'=0); 
  [] s=5 -> (s'=5);

endmodule

rewards
  true : 1;
endrewards
