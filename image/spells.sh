# Loads spell files for every act the cluster reports as unlocked.
# Sourced from the player's profile; runs before each prompt.
_kingdom_loaded_act=0

_kingdom_load_spells() {
  act=$(kubectl get configmap kingdom-state -n default -o jsonpath='{.data.act}' 2>/dev/null) || return 0
  case "$act" in
    ''|*[!0-9]*) return 0 ;;
  esac
  while [ "$_kingdom_loaded_act" -lt "$act" ]; do
    _kingdom_loaded_act=$((_kingdom_loaded_act + 1))
    spell_file=/etc/kingdom/spells.d/act$_kingdom_loaded_act.rc
    [ -f "$spell_file" ] && . "$spell_file"
  done
}

PROMPT_COMMAND=_kingdom_load_spells
