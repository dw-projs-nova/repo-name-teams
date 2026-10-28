# Instructions

Uses a SMTP server, I use **smtp4dev** for it.

You also need to change **.env.example** => **.env** so the app works.
###### Do not forget to set `ADMIN_EMAIL` to something!!

To run, do the following:
```sh
pip install -r requirements.txt
flask run --debug --reload --port 5001
```
smtp4dev is desktop/cli, use desktop for graphical interface and easier usage :) - `winget install "smtp4dev desktop"`*
#### *note that it does not install a shortcut but a command-line alias, I recommend that you go into its install directory and pin the desktop shortcut to your taskbar/start-menu

---

# Tools

- [smtp4dev](https://github.com/rnwood/smtp4dev)
- [heidisql](https://heidisql.com)


For heidi, do __**NOT**__ get the portable version!!! it misses all drivers except mysql/postgres, you will have to manually add them yourself!
