if {$argc < 3} {
    puts stderr "Usage: vmd -dispdev text -e extract_rdf.tcl -args <psf> <dcd> <output> ?first? ?last? ?step? ?delta? ?rmax?"
    quit 1
}

set psf_file [lindex $argv 0]
set dcd_file [lindex $argv 1]
set out_file [lindex $argv 2]

set first_frame 100
set last_frame -1
set frame_step 1
set delta 0.1
set rmax 12.0

if {$argc > 3} { set first_frame [lindex $argv 3] }
if {$argc > 4} { set last_frame [lindex $argv 4] }
if {$argc > 5} { set frame_step [lindex $argv 5] }
if {$argc > 6} { set delta [lindex $argv 6] }
if {$argc > 7} { set rmax [lindex $argv 7] }

mol new $psf_file type psf waitfor all
mol addfile $dcd_file type dcd waitfor all

set sel1 [atomselect top "name OH2"]
set sel2 [atomselect top "name OH2"]

set numframes [molinfo top get numframes]
if {$last_frame < 0} {
    set last_frame [expr {$numframes - 1}]
}

if {[catch {
    measure gofr $sel1 $sel2 delta $delta rmax $rmax usepbc 1 selupdate 0 first $first_frame last $last_frame step $frame_step
} rdf]} {
    puts stderr "RDF calculation failed: $rdf"
    quit 1
}

set radii [lindex $rdf 0]
set g_of_r [lindex $rdf 1]

set out [open $out_file w]
foreach radius $radii value $g_of_r {
    puts $out "$radius $value"
}
close $out

puts "Wrote RDF data to $out_file"
quit
