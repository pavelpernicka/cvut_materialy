function sys = hw_4_st(dd, mm, yy, varargin)
%	
%   hw_4_st    Data Generator for ARI2012 Homework No. 4 
%
%   The command
%       sys = hw_4_st(dd, mm, yy, varargin)
%   generates input data for ARI homework No.4 - 2012 from student's date of
%   birth
%
%	Summary: 
%		Run this function with date of birth of the student and function will return homework assignment.
%
%	Syntax: 
%       sys = hw_4_st(dd, mm, yy)
%       sys = hw_4_st(dd, mm, yy, 'display')
%
%
%	Inputs: 
%		required: 
%			date of birth (dd - day, mm - month, yy - year)
%		optional:
%			display - to display results
%
%	Outputs:
%		sys - system transfer function in zero-pole-gain format
%
%   Example:
%       >> sys = hw_4_st(25, 1, 54)
%
%       Zero/pole/gain:
%             1
%       ------------
%       (s+1) (s+24)
%
%       >> class(sys)
%       ans =
%       zpk

%			
%	Author: 
%		Kamil Dolinsky (last modified 28.2.2011)
%		MIchael Sebek  (modified 08-Feb-2012)

	[dd, mm, yy, display] = parseInput(dd, mm, yy, varargin{:});
	
	sys = zpk([],[-mm, -(6*(mm+round(dd/10)))],1);
	
	if display
		fprintf('Transfer function for assignment is \n')
		sys
	end
	
end

function [dd, mm, yy, display] = parseInput(dd, mm, yy, varargin)
	p = inputParser;
	p.addRequired('dd',@(x)isa(x,'numeric')&& size(x,1) == 1 && size(x,2) == 1 && x >= 1 && x <= 31 && mod(x,1) == 0);
	p.addRequired('mm',@(x)isa(x,'numeric')&& size(x,1) == 1 && size(x,2) == 1 && x >= 1 && x <= 12 && mod(x,1) == 0);
	p.addRequired('yy',@(x)isa(x,'numeric')&& size(x,1) == 1 && size(x,2) == 1 && x >= 0 && x <= 99 && mod(x,1) == 0);
	p.addOptional('display',nargout == 0,@(x)isa(x,'logical'));

	p.parse(dd, mm, yy, varargin{:});

	dd = p.Results.dd;
	mm = p.Results.mm;
	yy = p.Results.yy;
	display = p.Results.display;
end
