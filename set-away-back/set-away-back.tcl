# Fabulor-Name: Set Away-Back aliase
# Fabulor-Version: 1.0.0
# Fabulor-Description: Adds all-network away and back commands

namespace eval fabulor::addons::set-away-back {}

proc fabulor::addons::set-away-back::allaway {arguments} {
    set message [string trim $arguments]
    if {$message eq ""} {
        set message "I am away."
    }

    zoitechat::command ALLSERV AWAY $message
}

proc fabulor::addons::set-away-back::allback {arguments} {
    zoitechat::command ALLSERV BACK
}

proc init {} {
    zoitechat::register_command ALLAWAY fabulor::addons::set-away-back::allaway
    zoitechat::register_command ALLBACK fabulor::addons::set-away-back::allback
    zoitechat::log "Set-away-back initialised"
}
