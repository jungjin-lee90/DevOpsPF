#!/bin/bash
#export LANG=ko_KR.UTF-8
#export LC_ALL=ko_KR.UTF-8

echo "workspace : $WORKSPACE"
cd "$WORKSPACE"

# 최신 리비전 확인
REV_CUR=$(svn info svn+ssh://jungjin.lee@192.168.12.11/home/cvs/repos/GC4/trunk | grep ^리비전 | awk '{print $2}')
REV_PREV=$(($REV_CUR - 1))

echo "Revision : $REV_CUR"
echo "Revision Prev: $REV_PREV"

# 커밋 메시지, 작성자 추출
author=$(svn log svn+ssh://jungjin.lee@192.168.12.11/home/cvs/repos/GC4/trunk -r $REV_CUR --xml | grep "<author>" | sed -e 's/<[^>]*>//g')
msg=$(svn log svn+ssh://jungjin.lee@192.168.12.11/home/cvs/repos/GC4/trunk -r $REV_CUR --xml | grep "<msg>" | sed -e 's/<[^>]*>//g')

echo "Author : $author"
printf "Commit message : %s\n" "$msg"

# changelog.xml 생성
CHANGELOG_FILE="$WORKSPACE/changelog.xml"
svn log -r $REV_CUR --xml > "$CHANGELOG_FILE"
echo "Generated custom changelog.xml:"
cat "$CHANGELOG_FILE"

# 변경된 내용(diff) 보기 좋게 출력
echo "------------------------------------------------------------"
echo " 변경된 내용(diff): 리비전 $REV_PREV → $REV_CUR"
echo "------------------------------------------------------------"

svn diff -r $REV_PREV:$REV_CUR "$WORKSPACE" > "$WORKSPACE/svn-changes.diff"

if [ -s "$WORKSPACE/svn-changes.diff" ]; then
    cat "$WORKSPACE/svn-changes.diff"
else
    echo "변경된 파일이 없습니다."
fi

echo "------------------------------------------------------------"
echo "빌드 스크립트 완료"

