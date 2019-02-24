#!/usr/bin/perl -w

use strict;

# Check a TREC 2016 Real Time Summarization track, Scenario B
# submission for various common errors:
#      * extra fields
#      * multiple run tags
#      * unknown topics (missing topics allowed, since retrieving no docs
#        for a topic is a valid repsonse)
#      * invalid retrieved documents (approximate check)
#      * duplicate retrieved documents in a single topic
#      * too many documents retrieved for a topic
# Messages regarding submission are printed to an error log

# Results input file for Scenario B is of the form
#     YYYYMMDD topic-id Q0 tweet-id rank score tag

# For Scenario B, enforce at most 100 Tweets per day per topic.  This check
# uses the YYYMMDD given in the run.  Note that this does not check that
# the Tweet actually occurred on that date.  That is beyond the scope of the
# check script.  Also, we accept dates of 12 Aug since the date is the
# decision date and perhaps the decision was delayed past midnight of the
# final day in the evaluation period.

# Change this variable to the directory in which the error log
# should be put
my $errlog_dir = ".";

# If more than MAX_ERRORS errors, then stop processing; something drastically
# wrong with the file.
my $MAX_ERRORS = 25; 

my $MAX_RET = 100;		# maximum number of docs to retrieve per day

my @topics;

my %docnos;                     # hash of retrieved docnos
my (%numret,%daycounts);	# number of docs retrieved per topic (per day)
my ($results_file);		# input file to be checked; it is an
				# 	input argument to the script
my $line;			# current input line
my $line_num;			# current input line number
my $errlog;			# file name of error log
my $num_errors;			# flags for errors detected
my $topic;
my ($docno,$q0,$sim,$rank,$tag,$date,$time);
my $q0warn = 0;
my $run_id;
my ($i);

my $usage = "Usage: $0 resultsfile\n";
$#ARGV == 0 || die $usage;
$results_file = $ARGV[0];

open RESULTS, "<$results_file" ||
	die "Unable to open results file $results_file: $!\n";

my @path = split "/", $results_file;
my $base = pop @path;
$errlog = $errlog_dir . "/" . $base . ".errlog";
open ERRLOG, ">$errlog" ||
	die "Cannot open error log for writing\n";

# Initialize data structures used in checks
my @oldtopids = (226, 227, 228, 229, 230, 235, 236, 237, 239, 242, 243,
	246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 258, 259,  
	260, 262, 263, 264, 265, 266, 267, 268, 269, 271, 272, 276, 277,
        278, 281, 282, 283, 284, 285, 286, 287, 296, 298, 299, 302, 303,
	305, 306, 308, 312, 314, 315, 316, 317, 319, 320, 321, 324, 326,
        327, 328, 330, 331, 332, 333, 334, 335, 336, 338, 339, 340, 341, 
	342, 344, 345, 346, 348, 349, 350, 351, 352, 353, 354, 356, 357,
        358, 359, 361, 362, 363, 365, 366, 369, 370, 371, 372, 374, 375,
	376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 388, 389, 390,
	391, 392, 393, 394, 399, 400, 401, 405, 407, 408, 409, 410, 411,
	414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426,
	429, 430, 431, 432, 433, 434, 436, 437, 438, 439, 440, 441, 443,
	446, 448, 449, 450);
my @oldtopics = map { sprintf "MB%d", $_ } @oldtopids;
my @newtopics = map { sprintf "RTS%d", $_ } 1 .. 45;
@topics = (@oldtopics, @newtopics);
foreach $topic (@topics) {
    $numret{$topic} = 0;
    for ($i=2; $i<=12; $i++) {
 	$date = "201608$i";
        $daycounts{$topic}{$date} = 0;
    }
}

$num_errors = 0;
$line_num = 0;
$run_id = "";
while ($line = <RESULTS>) {
    chomp $line;
    next if ($line =~ /^\s*$/);

    undef $tag;
    my @fields = split " ", $line;
    $line_num++;
	
    if (scalar(@fields) == 7) {
       ($date,$topic,$q0,$docno,$rank,$sim,$tag) = @fields;
    } else {
       &error("Wrong number of fields (expecting 7)");
       exit 255;
    }

    # make sure runtag is ok
    if (! $run_id) { 	# first line --- remember tag 
	$run_id = $tag;
	if ($run_id !~ /^[A-Za-z0-9_.-]{1,15}$/) {
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

    # make sure topic is known
    if (!exists($numret{$topic})) {
	&error("Unknown topic '$topic'");
	$topic = 0;
	next;
    }  
    

    # make sure DOCNO known and not duplicated
    if ($docno =~ /^[0-9]{18}$/) {   # valid DOCNO to the extent we will check
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

    if ($q0 ne "Q0" && ! $q0warn) {
        $q0warn = 1;
        &error("Field 3 is `$q0' not `Q0'");
    }

    # remove leading 0's from rank (but keep final 0!)
    $rank =~ s/^0*//;
    if (! $rank) {
        $rank = "0";
    }

    # date has to be in correct format and refer to a date within
    # the evaluation period.
    my ($year,$month,$day);
    if ($date !~ /(\d\d\d\d)(\d\d)(\d\d)/) {
	&error("Date string $date not in correct format of YYYYMMDD");
	next;
    }
    $year = $1; $month = $2; $day = $3;
    if ($year ne "2016") {
	&error("Date $date has year $year, not 2016");
	next;
    }
    if ($month ne "08" ) {
	&error("Date $date has month $month, not 08");
	next;
    }
    if ($day < 2 || $day > 12) {
	&error("Date $date has day $day (must be between 2--12)");
	next;
    }

    $daycounts{$topic}{$date}++;
}


# Do global checks:
#   error if some topic has too many documents retrieved
foreach $topic (@topics) { 
    for ($i=2; $i<=12; $i++) {
	$date = sprintf "201608%02d", $i;
	if ($daycounts{$topic}{$date} > $MAX_RET) {
            &error("Too many documents ($daycounts{$topic}{$date}) retrieved for day $date for topic $topic");
	}
    }
}

print ERRLOG "Finished processing $results_file\n";
close ERRLOG || die "Close failed for error log $errlog: $!\n";

if ($num_errors) { exit 255; }
exit 0;


# print error message, keeping track of total number of errors
sub error {
   my $msg_string = pop(@_);

    print ERRLOG 
    "run $results_file: Error on line $line_num --- $msg_string\n";

    $num_errors++;
    if ($num_errors > $MAX_ERRORS) {
        print ERRLOG "$0 of $results_file: Quit. Too many errors!\n";
        close ERRLOG ||
		die "Close failed for error log $errlog: $!\n";
	exit 255;
    }
}
