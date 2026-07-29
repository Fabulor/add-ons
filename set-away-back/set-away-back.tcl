# Fabulor-Name: Set Away-Back aliase
# Fabulor-Version: 1.0.0
# Fabulor-Description: Adds all-network away and back commands

namespace eval fabulor::addons::set-away-back {}

proc fabulor::addons::set-away-back::allaway {arguments} {
    set message [string trim $arguments]
    if {$message eq ""} {
        set message "I am away."
    }

    fabulor::command ALLSERV AWAY $message
}

proc fabulor::addons::set-away-back::allback {arguments} {
    fabulor::command ALLSERV BACK
}

proc init {} {
    fabulor::register_command ALLAWAY fabulor::addons::set-away-back::allaway
    fabulor::register_command ALLBACK fabulor::addons::set-away-back::allback
    fabulor::log "Set-away-back initialised"
}
