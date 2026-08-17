# Fabulor-Name: Uptime
# Fabulor-Version: 1.0.7
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
  # Ask Fabulor for the Windows boot timer directly. This avoids a child
  # PowerShell process and the retired WMI/CIM query path.
  set uptime_seconds [fabulor::get_windows_uptime_seconds]
  if {![string is integer -strict $uptime_seconds]} {
    error "Fabulor returned an invalid Windows uptime value."
  }

  return [expr {wide($uptime_seconds)}]
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
