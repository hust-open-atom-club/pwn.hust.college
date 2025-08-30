贡献
================================================================================

如果你想要给 [pwn.hust.college](https://github.com/hust-open-atom-club/pwn.hust.college) 做贡献，请遵照如下规则：

1. 点击仓库主页右上角的 `fork` 按钮

2. 通过如下命令 `clone` 你 Github 帐号中的 `pwn.hust.college` 仓库：

    ```
    git clone git@github.com:<YOUR_GITHUB_USERNAME>/pwn.hust.college.git
    ```

3. 通过如下命令创建分支 (`branch`)：

    ```
    git checkout -b "fix:dojo-fix"
    ```
    其中，`fix:dojo-fix` 仅为一个 fix 样例。

4. 对本地仓库进行修改。

5. 提交自己的修改，然后推送 (`push`) 到远端。

    ```
    git add your_changed_files
	git commit -m "your comment"
    git push --set-upstream origin fix:dojo-fix
    ```

6. 点击 `New Pull Request` 按钮，将你 Github 帐号中的 `pwn.hust.college` 仓库的 `fix:dojo-fix` 分支的修改提交到当前 `pwn.hust.college` 库中。

请注意，如果之后想追加代码提交，你可以通过 push 新的代码提交到自己仓库的 `fix:dojo-fix` 分支，这些代码提交会直接同步到新建的 PR(Pull Request) 中。

7. 等待分支被 merge 或 reject 之后，该分支便可以删除了。

十分感谢！
