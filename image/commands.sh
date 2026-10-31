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

# Rewrites a typed line before it runs: maps synonyms to command names and drops filler words.
# Lines that don't start with a known command are returned unchanged, so raw kubectl still works.
_kingdom_normalize() {
  local line=$1 verb word
  local -a words out
  read -r -a words <<<"$line"
  [ "${#words[@]}" -gt 0 ] || { printf '%s' "$line"; return; }

  case "${words[0]}" in
    look|l) verb=lookaround ;;
    examine|x|read|check) verb=inspect ;;
    say|speak) verb=whisper ;;
    go|walk) verb=switch ;;
    *) verb=${words[0]} ;;
  esac
  alias "$verb" >/dev/null 2>&1 || { printf '%s' "$line"; return; }

  out=("$verb")
  for word in "${words[@]:1}"; do
    if [ "$verb" != whisper ]; then
      case "$word" in the|a|an|at|to|into) continue ;; esac
    fi
    out+=("$word")
  done
  printf '%s' "${out[*]}"
}

if [[ $- == *i* ]]; then
  _kingdom_rewrite_line() {
    READLINE_LINE=$(_kingdom_normalize "$READLINE_LINE")
    READLINE_POINT=${#READLINE_LINE}
  }
  bind -x '"\C-x\C-n": _kingdom_rewrite_line'
  # Enter first rewrites the line, then accepts it.
  bind '"\C-m": "\C-x\C-n\C-j"'
fi
