#!/usr/bin/perl -w

use strict;

# Check a TREC 2016 Task track, Task Completion or Web Ad Hoc Task
# submission for various common errors:
#      * extra fields
#      * multiple run tags
#      * missing or extraneous topics
#      * invalid retrieved documents
#      * duplicate retrieved documents in a single topic
#      * too many documents retrieved for a topic
# Messages regarding submission are printed to an error log

# Results input file is in the form
#     topic_num Q0 docno rank sim tag
#

# Change these variable values to the directory in which the error log
# should be put
my $errlog_dir = ".";

# If more than 25 errors, then stop processing; something drastically
# wrong with the file.
my $MAX_ERRORS = 25; 

my @topics;
my $MAX_RET = 1000;

my %docnos;                     # hash of all valid docnos
my %numret;			# number of docs retrieved per topic
my $results_file;		# input file to be checked
my $errlog;			# file name of error log
my ($q0warn, $num_errors);	# flags for errors detected
my $d;				# current docid
my $line;			# current input line
my ($q0,$docno,$rank,$sim,$tag,$rest);
my $line_num;			# current input line number
my ($topic, $old_topic);
my $run_id;
my $found;
my ($i,$t,$col1,$col2,$last_i);

my $usage = "Usage: $0 resultsfile\n";
$results_file = shift @ARGV or die $usage;

# Initialize data structures used in checks

@topics = 1 .. 50;

# number retrieved per topic
foreach $t (@topics) {
    $numret{$t} = 0;
}

open RESULTS, "<$results_file" ||
	die "Unable to open results file $results_file: $!\n";


my @path = split "/", $results_file;
my $base = pop @path;
$errlog = $errlog_dir . "/" . $base . ".errlog";
open ERRLOG, ">$errlog" ||
	die "Cannot open error log for writing\n";

$q0warn = 0;
$num_errors = 0;
$line_num = 0;
$old_topic = "-1";
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
    if (! $run_id) { 	# first line --- remember tag 
	$run_id = $tag;
	if ($run_id !~ /^[A-Za-z0-9_.]{1,20}$/) {
	    &error("Run tag `$run_id' is malformed");
	    next;
	}
    }
    else {			# otherwise just make sure one tag used
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
    

    # make sure DOCNO known and not duplicated
    if ($docno =~ /^clueweb12-\d{4}(wb|wt|tw)-\d{2}-\d{5}$/) {   # valid DOCNO
	if (exists $docnos{$docno} && $docnos{$docno} eq $topic) {
	    &error("Document `$docno' retrieved more than once for topic $topic");
	    next;
	}
	$docnos{$docno} = $topic;
    }
    else {				# invalid DOCNO
	&error("Unknown document `$docno'");
	next;
    }


    # remove leading 0's from rank (but keep final 0!)
    $rank =~ s/^0*//;
    if (! $rank) {
	$rank = "0";
    }

    $numret{$topic}++;
}


# Do global checks:
#   error if some topic has no (or too many) documents retrieved for it
#   warning if too few documents retrieved for a topic
foreach $t (@topics) { 
    if ($numret{$t} == 0) {
        &error("No documents retrieved for topic $t");
    }
    elsif ($numret{$t} > $MAX_RET) {
        &error("Too many documents ($numret{$t}) retrieved for topic $t");
    }
}
print ERRLOG "Finished processing $results_file\n";
close ERRLOG || die "Close failed for error log $errlog: $!\n";

if ($num_errors) { exit 255; }
exit 0;


# print error message, keeping track of total number of errors
# line numbers refer to SORTED file since that is the actual input file
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
