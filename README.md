# pft

Help message:
```
$ uv run pft --help
                                                                                                                                           
 Usage: pft [OPTIONS] COMMAND [ARGS]...                                                                                                    
                                                                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                 │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                          │
│ --help                        Show this message and exit.                                                                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ add                                                                                                                                     │
│ import                                                                                                                                  │
│ list                                                                                                                                    │
│ categorize                                                                                                                              │
│ summarize                                                                                                                               │
│ analyze                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

Help message for a certain command for usage:
```
$ uv run pft add --help
                                                                                                                                           
 Usage: pft add [OPTIONS]                                                                                                                  
                                                                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --desc            <str>  Transaction description [required]                                                                          │
│ *  --amt             <str>  Transaction amount, positive as income, negative as expense, rounded to the nearest cent [required]         │
│    --date            <str>  YYYY-MM-DD, default as today                                                                                │
│    --category        <str>  Optional category                                                                                           │
│    --help                   Show this message and exit.                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```