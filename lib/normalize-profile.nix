# Production dual reader. New profiles use schema 3; existing schemas stay explicit.
{catalog}: profile:
if builtins.isAttrs profile && builtins.isInt (profile.schema or null) && profile.schema == 3
then (import ./profile-drafts {inherit catalog;}).normalize profile
else (import ./normalize-profile-v2.nix {inherit catalog;}) profile
