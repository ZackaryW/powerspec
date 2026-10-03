# Worksets

Powerspec uses OpenSpec's saved worksets as input and creates separate implementation worktrees. Git owns branches and checkout metadata; OpenSpec owns membership and editor opening.

```sh
pspec workset add project --path /repos/api
pspec workset launch project --branch feature/payments
pspec workset launch project --branch feature/payments --repo1 api --branch1 feature/backend --remote1 origin/main --worktree1 api-payments
```

All source members launch. Numbered groups override members by their OpenSpec label; positive indices may have gaps. `--repo1=api` is also accepted. Repeated fields, unknown options and conflicting aliases are errors. A subfolder resolves to its Git checkout; aliases of the same Git repository collapse to the first label and position.

New branches start from local `main`, or the explicit local remote-tracking ref supplied by `--remoteN`. Launch never fetches. Existing branches are preserved; a remote override conflicts with an existing branch unless its matching worktree already exists. A matching worktree is reused even after commits or local edits. Source checkouts remain unchanged except for an explicitly requested change move.

The default directory is a sibling of the original checkout: `<repo>-<branch-token>`. Tokens are lowercase, with runs outside ASCII letters, numbers and hyphens replaced by a hyphen and leading/trailing hyphens removed. Empty tokens and conflicting destinations fail. `--worktreeN` supplies a safe single directory name. The output workset is `<source>-<shared-branch-token>`, or `--name <name>`; per-repository branch overrides do not change that name. OpenSpec names must be lowercase kebab-case.

Registration compatibility: the currently supported OpenSpec CLI has `workset list/create` but no supported member-append operation. Adding a first repository works; adding the same repository again is a no-op. Adding another repository to an existing workset reports the missing upstream API without changing membership. Until that API exists, compose multi-repository source worksets with OpenSpec's `workset create --member label=path` options. Powerspec never edits OpenSpec's registry or deletes and recreates worksets.

Successful launch prints `openspec workset open <output> --tool code`. Run that command to open the collection. Powerspec does not launch an editor.
