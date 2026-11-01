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

PS0='\n'
PROMPT_COMMAND='printf "\n"; _kingdom_load_commands'
alias k=kubectl

# Rewrites a typed line before it runs: maps synonyms to command names and drops filler words.
# Lines that don't start with a known command are returned unchanged, so raw kubectl still works.
_kingdom_normalize() {
  local line=$1 verb word
  local -a words out
  read -r -a words <<<"$line"
  [ "${#words[@]}" -gt 0 ] || { printf '%s' "$line"; return; }
  case "${words[0]:-}" in hey,|hi,) words[0]=${words[0]%,} ;; esac
  case "${words[0]}" in say|speak) words=("${words[@]:1}") ;; esac
  if [ "${words[0]:-}" = open ] && [ "${words[1]:-}" = k8s ]; then
    words=(openk8s "${words[@]:2}")
  fi

  case "${words[0]}" in
    k) printf '%s' "$line"; return ;;
    look|l) verb=lookaround ;;
    examine|x|read|check) verb=inspect ;;
    go|walk) verb=switch ;;
    *) verb=${words[0]} ;;
  esac
  { alias "$verb" || declare -F "$verb"; } >/dev/null 2>&1 || { printf '%s' "$line"; return; }

  out=("$verb")
  for word in "${words[@]:1}"; do
    if [ "$verb" != openk8s ]; then
      case "$word" in the|a|an|at|to|into|on|in|of|for) continue ;; esac
    fi
    out+=("$word")
  done
  printf '%s' "${out[*]}"
}

if [[ $- == *i* ]]; then
  _kingdom_rewrite_line() {
    if [ "$READLINE_LINE" != exit ]; then _kingdom_exit_armed=; fi
    READLINE_LINE=$(_kingdom_normalize "$READLINE_LINE")
    READLINE_POINT=${#READLINE_LINE}
  }
  exit() {
    if [ -n "$_kingdom_exit_armed" ]; then
      builtin exit
    fi
    _kingdom_exit_armed=1
    echo "Leaving the kingdom now will end your game. Type exit again to leave."
  }
  bind -x '"\C-x\C-n": _kingdom_rewrite_line'
  # Enter first rewrites the line, then accepts it.
  bind '"\C-m": "\C-x\C-n\C-j"'
fi

_kingdom_help_entries=()

_kingdom_describe() {
  _kingdom_help_entries+=("$1|$2|$3")
}

help() {
  local ns entry name nss desc
  ns=$(kubectl config view --minify -o jsonpath='{..namespace}' 2>/dev/null)
  ns=${ns:-default}
  for entry in "${_kingdom_help_entries[@]}"; do
    IFS='|' read -r name nss desc <<<"$entry"
    case " $nss " in
      *" $ns "*) printf '  %-10s %s\n' "$name" "$desc" ;;
    esac
  done
}

_kingdom_describe help "default village" "show the commands available here"
_kingdom_describe exit "default village" "leave the game"
