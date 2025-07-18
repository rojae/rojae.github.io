## Ubuntu login
```sh
proot-distro login ubuntu
```

## Jekyll Install
```sh
pkg update
pkg install tsu
pkg install ruby git build-essential
gem install jekyll bundler
pkg install git ruby clang make
echo 'export GEM_HOME=$HOME/.gem' >> ~/.profile
echo 'export PATH=$HOME/.gem/bin:$PATH' >> ~/.profile
source ~/.profile
gem install bundler jekyll
```

## Run jekyll server
```
bundle install
bundle exec jekyll serve
```