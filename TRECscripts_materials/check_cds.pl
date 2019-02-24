#!/usr/bin/perl -w

use strict;

# Check a TREC 2016 clinical decision support track submission for various
# common errors:
#      * extra fields
#      * multiple run tags
#      * missing or extraneous topics
#      * invalid retrieved documents (approximate check)
#      * duplicate retrieved documents in a single topic
#      * too many documents retrieved for a topic
#      * fewer than maximum allowed retrieved for a topic (warning)
# Messages regarding submission are printed to an error log

# Results input file is in the form
#     topic_num Q0 visitID rank sim tag

# Change this variable value to the directory where the error log should be put
my $errlog_dir = ".";


# If more than MAX_ERRORS errors, then stop processing; something drastically
# wrong with the file.
my $MAX_ERRORS = 25; 
# May return up to MAX_RET visit ids per topic
my $MAX_RET = 1000;

my @topics;
my %numret;                     # number of docs retrieved per topic
my %valid_ids;			# set of valid visit ids read from docno file
my $results_file;               # input file to be checked
my $errlog;                     # file name of error log
my ($q0warn, $num_errors);      # flags for errors detected
my $line;                       # current input line
my ($topic,$q0,$docno,$rank,$sim,$tag);
my $line_num;                   # current input line number
my $run_id;
my ($i,$t,$last_i);

my $usage = "Usage: $0 resultsfile\n";
$results_file = shift or die $usage;

@topics = 1 .. 30;

open RESULTS, "<$results_file" ||
    die "Unable to open results file $results_file: $!\n";

$last_i = -1;
while ( ($i=index($results_file,"/",$last_i+1)) > -1) {
    $last_i = $i;
}
$errlog = $errlog_dir . "/" . substr($results_file,$last_i+1) . ".errlog";
open ERRLOG, ">$errlog" ||
    die "Cannot open error log for writing\n";

    
for my $t (@topics) {
    $numret{$t} = 0;
}
$q0warn = 0;
$num_errors = 0;
$line_num = 0;
$run_id = "";

while ($line = <RESULTS>) {
    chomp $line;
    next if ($line =~ /^\s*$/);

    undef $tag;
    my @fields = split " ", $line;
    $line_num++;
	
    if (scalar(@fields) == 6) {
	($topic,$q0,$docno,$rank,$sim,$tag) = @fields;
    } else {
	&error("Wrong number of fields (expecting 6)");
	exit 255;
    }
	
    # make sure runtag is ok
    if (! $run_id) {		# first line --- remember tag 
	$run_id = $tag;
	if ($run_id !~ /^[A-Za-z0-9]{1,12}$/) {
	    &error("Run tag `$run_id' is malformed");
	    next;
	}
    }
    else {		       # otherwise just make sure one tag used
	if ($tag ne $run_id) {
	    &error("Run tag inconsistent (`$tag' and `$run_id')");
	    next;
	}
    }
	
    # get topic number
    if (!exists($numret{$topic})) {
	&error("Unknown topic ($topic)");
	$topic = 0;
	next;
    }
	
	
    # make sure second field is "Q0"
    if ($q0 ne "Q0" && ! $q0warn) {
	$q0warn = 1;
	&error("Field 2 is `$q0' not `Q0'");
    }
    
    # remove leading 0's from rank (but keep final 0!)
    $rank =~ s/^0*//;
    if (! $rank) {
	$rank = "0";
    }
	
    # make sure rank is an integer (a past group put sim in rank field by accident)
    if ($rank !~ /^[0-9-]+$/) {
	&error("Column 4 (rank) `$rank' must be an integer");
    }
	
    # make sure DOCNO has right format and not duplicated
    if (check_docno($docno)) {
	if (exists $valid_ids{$docno} && $valid_ids{$docno} == $topic) {
	    &error("$docno retrieved more than once for topic $topic");
	    next;
	}
	$valid_ids{$docno} = $topic;
    } else {
	&error("Unknown document id `$docno'");
	next;
    }
    $numret{$topic}++;
	
}



# Do global checks:
#   error if some topic has no (or too many) documents retrieved for it
#   warn if too few documents retrieved for a topic
foreach $t (@topics) {
    if ($numret{$t} == 0) {
        &error("No documents retrieved for topic $t");
    }
    elsif ($numret{$t} > $MAX_RET) {
        &error("Too many documents ($numret{$t}) retrieved for topic $t");
    }
    elsif ($numret{$t} < $MAX_RET) {
        print ERRLOG "$0 of $results_file:  WARNING: only $numret{$t} documents retrieved for topic $t\n"
    }
}


print ERRLOG "Finished processing $results_file\n";
close ERRLOG || die "Close failed for error log $errlog: $!\n";
if ($num_errors) {
    exit 255;
}
exit 0;


# print error message, keeping track of total number of errors
sub error {
    my $msg_string = pop(@_);

    print ERRLOG 
	"$0 of $results_file: Error on line $line_num --- $msg_string\n";

    $num_errors++;
    if ($num_errors > $MAX_ERRORS) {
        print ERRLOG "$0 of $results_file: Quit. Too many errors!\n";
        close ERRLOG ||
	    die "Close failed for error log $errlog: $!\n";
	exit 255;
    }
}


# Check for a valid visit id
#
sub check_docno {
    my ($docno) = @_;

    return ($docno =~ /^[\d+]{5,}$/); 
}

