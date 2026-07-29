# Fabulor-Name: Uptime
# Fabulor-Version: 1.0.0
# Fabulor-Description: Uptime command for Fabulor.

namespace eval fabulor::addons::uptime {}

proc fabulor::addons::uptime::bold {} {
  return "\002"
}

proc fabulor::addons::uptime::format_uptime {total_seconds} {
  set seconds [expr {wide($total_seconds)}]
  if {$seconds < 0} {
    set seconds 0
  }

  set weeks [expr {$seconds / 604800}]
  set days [expr {($seconds / 86400) % 7}]
  set hours [expr {($seconds / 3600) % 24}]
  set minutes [expr {($seconds / 60) % 60}]
  set remainder [expr {$seconds % 60}]

  set parts ""
  set started 0
  if {$weeks > 0} {
    append parts "${weeks}w"
    set started 1
  }
  if {$days > 0 || $started} {
    if {$parts ne ""} {
      append parts " "
    }
    append parts "${days}d"
    set started 1
  }
  if {$hours > 0 || $started} {
    if {$parts ne ""} {
      append parts " "
    }
    append parts "${hours}h"
    set started 1
  }
  if {$minutes > 0 || $started} {
    if {$parts ne ""} {
      append parts " "
    }
    append parts "${minutes}m"
    set started 1
  }
  if {$parts ne ""} {
    append parts " "
  }
  append parts "${remainder}s"

  return $parts
}

proc fabulor::addons::uptime::get_windows_uptime_seconds {} {
  set tick_script [join [list \
    {[Console]::OutputEncoding=[System.Text.Encoding]::UTF8} \
    {Write-Output ("TICKCOUNT64=" + [Environment]::TickCount64)} \
  ] {; }]

  set commands [list \
    [list powershell -NoProfile -NonInteractive \
      -ExecutionPolicy Bypass \
      -Command $tick_script] \
    [list pwsh -NoProfile -NonInteractive \
      -Command $tick_script] \
    [list wmic os get LastBootUpTime /value] \
    [list cmd /c wmic os get LastBootUpTime /value]
  ]
  set labels [list powershell pwsh wmic cmd]

  set diagnostics {}
  for {set i 0} {$i < [llength $commands]} {incr i} {
    set command [lindex $commands $i]
    set label [lindex $labels $i]

    if {[catch {
      set output [string trim [exec -- {*}$command]]
    } exec_error]} {
      lappend diagnostics "$label failed: $exec_error"
      continue
    }

    # WMIC LastBootUpTime path.
    if {[regexp {LastBootUpTime=([0-9]{14})} $output -> boot_stamp]} {
      if {[catch {
        set boot_epoch [clock scan $boot_stamp -format "%Y%m%d%H%M%S"]
      } parse_error]} {
        lappend diagnostics "$label parse failed: $parse_error"
        continue
      }

      set uptime [expr {[clock seconds] - $boot_epoch}]
      if {$uptime < 0} {
        set uptime 0
      }
      return $uptime
    }

    # TickCount64 path.
    if {[regexp {^TICKCOUNT64=([0-9]+)$} $output -> tick_ms]} {
      return [expr {wide($tick_ms) / 1000}]
    }

    if {[regexp {^([0-9]+)$} $output -> tick_ms]} {
      return [expr {wide($tick_ms) / 1000}]
    }

    if {$output eq ""} {
      lappend diagnostics "$label returned empty output"
    } else {
      lappend diagnostics "$label returned unrecognised output: $output"
    }
  }

  error "Unable to determine Windows uptime ([join $diagnostics {; }])"
}

proc fabulor::addons::uptime::uptime {arguments} {
  set mode [string tolower [string trim $arguments]]
  if {$mode eq ""} {
    set mode "auto"
  }

  if {$mode ni {auto say local}} {
    fabulor::print "Usage: /UPTIME ?auto|say|local?"
    return
  }

  if {[catch {
    fabulor::addons::uptime::get_windows_uptime_seconds
  } uptime_result]} {
    fabulor::print "Unable to get Windows uptime: $uptime_result"
    return
  }

  set uptime_seconds $uptime_result

  set nick "Me"
  array set user [fabulor::get_user_info]
  if {[info exists user(nick)] && $user(nick) ne ""} {
    set nick $user(nick)
  }

  set channel ""
  if {[info exists user(channel)] && $user(channel) ne ""} {
    set channel $user(channel)
  }

  set network ""
  if {[info exists user(network)] && $user(network) ne ""} {
    set network $user(network)
  }

  set bold_code [fabulor::addons::uptime::bold]
  set uptime_text [fabulor::addons::uptime::format_uptime $uptime_seconds]
  set text "${bold_code}${nick}'s Uptime:${bold_code} $uptime_text"
  set text [string map [list "{" "" "}" ""] $text]

  if {$mode eq "local"} {
    if {$network ne ""} {
      fabulor::print "($network) $text"
    } else {
      fabulor::print $text
    }
    return
  }

  if {$channel ne ""} {
    fabulor::send_message $channel $text
  } else {
    # No active channel (for example, server tab): keep output local.
    if {$network ne ""} {
      fabulor::print "($network) $text"
    } else {
      fabulor::print $text
    }
  }
}

proc init {} {
  fabulor::register_command UPTIME fabulor::addons::uptime::uptime
  fabulor::log "Uptime add-on initialised"
}
