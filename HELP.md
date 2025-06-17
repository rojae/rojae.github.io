## Command line
### run
```sh
bundle exec jekyll serve
```

### build
```sh
bundle exec jekyll build
```

### Total
```sh
# Homebrew로 Ruby 설치
brew install ruby

# PATH 설정 (필요 시)
echo 'export PATH="/opt/homebrew/opt/ruby/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Jekyll & Bundler 설치
gem install bundler jekyll

# 새 프로젝트 생성 (예시)
jekyll new my-blog
cd my-blog

git clone https://github.com/사용자명/블로그테마.git
cd 블로그테마

bundle install

bundle exec jekyll serve
```

### prompt
```
tip, info, warning, and danger
```