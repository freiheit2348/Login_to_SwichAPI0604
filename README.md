ログイン機能とスイッチAPI

Google Cloudを通してGoogleアカウントの認証機能が備わっています。
![image](https://github.com/freiheit2348/Login_to_SwichAPI0604/assets/116003620/ff096177-bda3-4acd-b684-c5f5ebdf57b7)

認証が完了後、Sign inのページへ移行します。
ここで自身のユーザー名とパスワードを設定します。
![image](https://github.com/freiheit2348/Login_to_SwichAPI0604/assets/116003620/3ab71c2b-36cf-42c8-87f4-39b43e6d7d5e)

次にログインページに移行し、先ほど設定したユーザー名とパスワードを入力します。
この二つはGoogleアカウントと紐づいているため、設定したグーグルアカウントからでないとアクセスすることができません。
![image](https://github.com/freiheit2348/Login_to_SwichAPI0604/assets/116003620/f77ac95a-0748-4cce-9923-2307538444f6)

登録された情報は同フォルダにあるregistered.jsonに記憶されるようになっております。

ログインが完了すると以下のページから変更可能なAPIの実行ページが表示されます。
open AI, Anthropic, Geminiが利用できます。
![image](https://github.com/freiheit2348/Login_to_SwichAPI0604/assets/116003620/65cb1834-9647-4034-9630-c93fae9f4156)

現状、パスワードまたはユーザー名を忘れた場合の再設定機能の実装を試みています。
