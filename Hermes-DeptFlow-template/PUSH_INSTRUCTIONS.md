# How to apply and push

I could not push from the execution environment, because outbound GitHub access is unavailable here.

Use this package as follows:

```bash
unzip deptflow-hermes-ready.zip
cd Hermes-DeptFlow-ready
./apply_to_repo.sh /path/to/deptflowhermes
cd /path/to/deptflowhermes
git add Hermes-DeptFlow
git commit -m "Build functional DeptFlow Hermes SDR profile template"
git push origin main
```

Then on the Hermes machine:

```bash
git clone https://github.com/eliottecs-stack/deptflowhermes.git
cp -r deptflowhermes/Hermes-DeptFlow/template_prospection ~/.hermes/profiles/client-demo
cd ~/.hermes/profiles/client-demo
cp .env.template .env
python3 scripts/validate_config.py
python3 scripts/dry_run.py --limit 5
```

The profile is dry-run by default and does not use Sales Navigator.
