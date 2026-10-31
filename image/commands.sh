# Loads command files for every act the cluster reports as unlocked.
# Sourced from the player's profile; runs before each prompt.
_kingdom_loaded_act=0

_kingdom_load_commands() {
  act=$(kubectl get configmap kingdom-state -n default -o jsonpath='{.data.act}' 2>/dev/null) || return 0
  case "$act" in
    ''|*[!0-9]*) return 0 ;;
  esac
  while [ "$_kingdom_loaded_act" -lt "$act" ]; do
    _kingdom_loaded_act=$((_kingdom_loaded_act + 1))
    command_file=/etc/kingdom/commands.d/act$_kingdom_loaded_act.rc
    [ -f "$command_file" ] && . "$command_file"
  done
}

PROMPT_COMMAND=_kingdom_load_commands
