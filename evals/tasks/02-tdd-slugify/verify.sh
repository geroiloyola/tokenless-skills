set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from slug import slugify
assert slugify("Héllo, World!") == "hello-world", slugify("Héllo, World!")
assert slugify("  A  B  ") == "a-b", slugify("  A  B  ")
assert slugify("Ça_va?") == "ca-va", slugify("Ça_va?")
EOF
