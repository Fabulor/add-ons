# Fabulor-Name: Kick Ban
# Fabulor-Version: 1.0.0
# Fabulor-Description: Adds KB and KBN helper commands for channel moderation

namespace eval fabulor::addons::kick_ban {}

proc fabulor::addons::kick_ban::parse_target_and_reason {arguments default_reason} {
    set input [string trim $arguments]
    if {$input eq ""} {
        return [list "" $default_reason]
    }

    set parts [split $input]
    set nick [lindex $parts 0]
    set reason [string trim [join [lrange $parts 1 end] " "]]
    if {$reason eq ""} {
        set reason $default_reason
    }

    return [list $nick $reason]
}

proc fabulor::addons::kick_ban::validate_target {command_name nick} {
    if {$nick eq ""} {
        zoitechat::print "Usage: /$command_name <nick> ?reason?"
        return 0
    }

    array set user [zoitechat::get_user_info]
    if {[info exists user(nick)] && [zoitechat::nickcmp $nick $user(nick)] == 0} {
        zoitechat::print "Trying to kick yourself is not healthy!"
        return 0
    }

    return 1
}

proc fabulor::addons::kick_ban::kb {arguments} {
    lassign [fabulor::addons::kick_ban::parse_target_and_reason \
        $arguments "Go to bed, stupido!"] nick reason

    if {![fabulor::addons::kick_ban::validate_target KB $nick]} {
        return
    }

    zoitechat::command BAN $nick 3
    zoitechat::command KICK $nick $reason
}

proc fabulor::addons::kick_ban::kbn {arguments} {
    lassign [fabulor::addons::kick_ban::parse_target_and_reason \
        $arguments "This nickname is forbidden! Please change it and come back again."] nick reason

    if {![fabulor::addons::kick_ban::validate_target KBN $nick]} {
        return
    }

    zoitechat::command BAN ${nick}!*@*
    zoitechat::command KICK $nick $reason
}

proc init {} {
    zoitechat::register_command KB fabulor::addons::kick_ban::kb
    zoitechat::register_command KBN fabulor::addons::kick_ban::kbn
    zoitechat::log "Kick-ban aliases initialised"
}