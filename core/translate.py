import re


class Translator:
    def __init__(self, text):
        self.text = text
        self.parted_text = self.text.split('\r\n')
        self.header = []

    # 줄 별로 처리해야 하는 메소드 (먼저 실행)
    def make_multiple_line(self, tag, pattern):
        previous = False
        new_parted_text = []
        rule = re.compile('^{0} (?P<string>.*)'.format(pattern))
        rule_of_previous = re.compile('(?P<string>.*)</{0}>'.format(tag))
        for line in self.parted_text:
            if rule.search(line) is not None:
                if previous:
                    new_parted_text[len(new_parted_text) - 1] = rule_of_previous.sub('\g<string>', new_parted_text[len(new_parted_text) - 1])
                    new_parted_text.append(rule.sub('\g<string></{0}>'.format(tag), line))
                else:
                    new_parted_text.append(rule.sub('<{0}>\g<string></{0}>'.format(tag), line))
                previous = True
            else:
                new_parted_text.append(line)
                previous = False
        self.parted_text = new_parted_text

    def make_header(self):
        new_parted_text = []

        h1 = re.compile('^#(?P<header>[^#]+)$')
        h2 = re.compile('^##(?P<header>[^#]+)$')
        h3 = re.compile('^###(?P<header>[^#]+)$')
        h4 = re.compile('^####(?P<header>[^#]+)$')
        h5 = re.compile('^#####(?P<header>[^#]+)$')
        h6 = re.compile('^######(?P<header>[^#]+)$')

        count = [0, 0, 0, 0, 0, 0]
        wanted_header = 1

        # 제목 처리를 함
        for line in self.parted_text:
            if wanted_header >= 1:
                matched = h1.search(line)
                if matched:
                    self.header.append([matched.group('header')])
                    count = [count[0] + 1, 0, 0, 0, 0, 0]
                    line = h1.sub('<h1><a id="section{0}" href="#index">{0}.<a> \g<header></h1>'.format(count[0]), line)
                    wanted_header = 2
                    new_parted_text.append(line)
                    continue
            if wanted_header >= 2:
                matched = h2.search(line)
                if matched:
                    self.header[count[0] - 1].append([matched.group('header')])
                    count = [count[0], count[1] + 1, 0, 0, 0, 0]
                    line = h2.sub('<h2><a id="section{0}.{1}" href="#index">{0}.{1}.</a> \g<header></h2>'.format(count[0], count[1]), line)
                    wanted_header = 3
                    new_parted_text.append(line)
                    continue
            if wanted_header >= 3:
                matched = h3.search(line)
                if matched:
                    self.header[count[0] - 1][count[1]].append([matched.group('header')])
                    count = [count[0], count[1], count[2] + 1, 0, 0, 0]
                    line = h3.sub('<h3><a id="section{0}.{1}.{2}" href="#index">{0}.{1}.{2}.</a> \g<header></h3>'.format(count[0], count[1], count[2]), line)
                    wanted_header = 4
                    new_parted_text.append(line)
                    continue
            if wanted_header >= 4:
                matched = h4.search(line)
                if matched:
                    self.header[count[0] - 1][count[1]][count[2]].append([matched.group('header')])
                    count = [count[0], count[1], count[2], count[3] + 1, 0, 0]
                    line = h4.sub('<h4><a id="section{0}.{1}.{2}.{3}" href="#index">{0}.{1}.{2}.{3}.</a> \g<header></h4>'.format(count[0], count[1], count[2], count[3]),
                                  line)
                    wanted_header = 5
                    new_parted_text.append(line)
                    continue
            if wanted_header >= 5:
                matched = h5.search(line)
                if matched:
                    self.header[count[0] - 1][count[1]][count[2]][count[3]].append([matched.group('header')])
                    count = [count[0], count[1], count[2], count[3], count[4] + 1, 0]
                    line = h5.sub(
                        '<h5><a id="section{0}.{1}.{2}.{3}.{4}" href="#index">{0}.{1}.{2}.{3}.{4}.</a> \g<header></h5>'.format(count[0], count[1], count[2], count[3],
                                                                         count[4]), line)
                    wanted_header = 6
                    new_parted_text.append(line)
                    continue
            if wanted_header >= 6:
                matched = h6.search(line)
                if matched:
                    self.header[count[0] - 1][count[1]][count[2]][count[3]][count[4]].append(matched.group('header'))
                    count = [count[0], count[1], count[2], count[3], count[4], count[5] + 1]
                    line = h5.sub('<h6><a id="section{0}.{1}.{2}.{3}.{4}.{5}" href="#index">{0}.{1}.{2}.{3}.{4}.{5}.</a> \g<header></h6>'
                                  .format(count[0], count[1], count[2], count[3], count[4], count[5]), line)
                    new_parted_text.append(line)
                    continue
            new_parted_text.append(line)
        self.parted_text = new_parted_text

    def make_block_element(self):
        # 목차를 삽입합니다.
        new_parted_text = []
        if re.search('\[목차\]', self.text):
            index_string = self.make_index()
            index_rule = re.compile('^\[목차\]$')
            for line in self.parted_text:
                new_parted_text.append(index_rule.sub(index_string, line))
            self.parted_text = new_parted_text
        # 구분선을 삽입합니다.
        new_parted_text = []
        hr_rule = re.compile('^-----*$')
        for line in self.parted_text:
            new_parted_text.append(hr_rule.sub('<hr>', line))
        self.parted_text = new_parted_text

    def make_list(self):
        # unordered list
        previous = False
        new_parted_text = []
        rule = re.compile('^\* (?P<string>.*)')
        rule_of_previous = re.compile('(?P<string>.*)</ul>')
        for line in self.parted_text:
            if rule.search(line) is not None:
                if previous:
                    new_parted_text[len(new_parted_text) - 1] = rule_of_previous.sub('\g<string>',
                                                                                     new_parted_text[len(new_parted_text) - 1])
                    new_parted_text.append(rule.sub('<li>\g<string></li></ul>', line))
                else:
                    new_parted_text.append(rule.sub('<ul><li>\g<string></li></ul>', line))
                previous = True
            else:
                new_parted_text.append(line)
                previous = False
        self.parted_text = new_parted_text

        # ordered list
        previous = 0
        new_parted_text = []
        rule = re.compile('^(?P<number>[0-9]+)\. (?P<string>.*)')
        rule_of_previous = re.compile('(?P<string>.*)</ol>')
        for line in self.parted_text:
            element = rule.search(line)
            if element is not None and previous + 1 == int(element.group('number')):
                if previous > 0:
                    new_parted_text[len(new_parted_text) - 1] = rule_of_previous.sub('\g<string>',
                                                                                     new_parted_text[len(new_parted_text) - 1])
                    new_parted_text.append(rule.sub('<li>\g<string></li></ol>', line))
                else:
                    new_parted_text.append(rule.sub('<ol><li>\g<string></li></ol>', line))
                previous = previous + 1
            else:
                new_parted_text.append(line)
                previous = 0
        self.parted_text = new_parted_text

    def make_table(self):
        def table_maker(data, size):
            table = '<table>'
            table_reference = [[[-1, 1, 1] for col in range(size[1])] for row in range(size[0])] # [상태, row, col] -1 : 아직 안 됨, 0 : 확장되는 부분, 1 : 참조할 데이터가 있음
            align_rule = re.compile('^({(?P<align>left|center|right)} )?(?P<data>.*)')

            for row in range(size[0]):
                for col in range(size[1]):
                    data[row][col] = data[row][col].rstrip()
                    if table_reference[row][col][0] == -1:
                        if col != 0 and data[row][col] == '>>':
                            count = 1
                            for index in range(col + 1, size[1]):
                                if data[row][index] == '>>':
                                    count += 1
                                    table_reference[row][index][0] = 0
                                else:
                                    break
                            table_reference[row][col][0] = 0
                            table_reference[row][col - 1][2] += count
                        elif row != 0 and data[row][col] == 'VV':
                            count = 1
                            for index in range(row + 1, size[0]):
                                if data[index][col] == 'VV':
                                    count += 1
                                    table_reference[index][row][0] = 0
                                else:
                                    break
                            table_reference[row][col][0] = 0
                            table_reference[row - 1][col][1] += count
                        else:
                            table_reference[row][col][0] = 1
            for row in range(size[0]):
                table += '<tr>'
                for col in range(size[1]):
                    if table_reference[row][col][0] == 1:
                        element = align_rule.search(data[row][col]).group('data', 'align')
                        style = ''
                        if element[1] is not None:
                            style = ' style="text-align: ' + element[1] + ';"'
                        span = []
                        if table_reference[row][col][1] > 1:
                            span.append('rowspan="{0}"'.format(table_reference[row][col][1]))
                        if table_reference[row][col][2] > 1:
                            span.append('colspan="{0}"'.format(table_reference[row][col][2]))
                        if span:
                            span = " " + " ".join(span)
                        else:
                            span = ""
                        table += '<th{0}{1}>{2}</th>'.format(span, style, element[0])
                table += '</tr>'
            table += '</table>'
            return table

        previous = False
        new_parted_text = []
        table_rule = re.compile('^\|\|(?P<data>.*)\|\|$')
        table_size = [0, 0] # table size [row, col]
        table_data = []
        for line in self.parted_text:
            line_data = table_rule.search(line)
            if line_data is not None:
                line_data = line_data.group('data').split('||')
                if previous:
                    if len(line_data) == table_size[1]:
                        table_size[0] += 1
                        table_data.append(line_data)
                        continue
                    else:
                        new_parted_text.append(table_maker(table_data, table_size))
                        table_size = [0, 0]
                        table_data = []
                table_size = [table_size[0] + 1, len(line_data)]
                table_data.append(line_data)
                previous = True
            else:
                if previous:
                    new_parted_text.append(table_maker(table_data, table_size))
                    table_size = [0, 0]
                    table_data = []
                new_parted_text.append(line)
                previous = False
        if previous:
            new_parted_text.append(table_maker(table_data, table_size))
        self.parted_text = new_parted_text

    def make_link(self):  # [[내용]] 꼴을 처리함
        new_parted_text = []
        expression = re.compile('\[\[((?P<title>.+?)\|)?(?P<link>.+?)\]\]')
        http_pattern = re.compile('^https?://')
        for line in self.parted_text:
            searched_line = expression.search(line)
            if searched_line is not None:
                if http_pattern.search(searched_line.group('link')) is not None: #http 링크임
                    if searched_line.group('title') is not None:
                        line = expression.sub('<a href="\g<link>">\g<title></a>', line)
                    else:
                        line = expression.sub('<a href="\g<link>">\g<link></a>', line)
                else:
                    if searched_line.group('title') is not None:
                        line = expression.sub('<a href="/doc/\g<link>">\g<title></a>', line)
                    else:
                        line = expression.sub('<a href="/doc/\g<link>">\g<link></a>', line)
            new_parted_text.append(line)

        self.parted_text = new_parted_text

    # 한 번에 처리하는 메소드 (나중에 실행)
    def make_single_line(self, tag, pattern1, pattern2):
        if pattern1 == '//': # 여러 프로토콜 형식이 ://와 같은 형식을 사용해서 에러를 방지합니다.
            self.text = re.sub('(?<!:){0}(?P<string>.*?){0}'.format(pattern1),
                               '<{0}>\g<string></{0}>'.format(tag), self.text)
        else:
            self.text = re.sub('{0}(?P<string>.*?){1}'.format(pattern1, pattern2),
                               '<{0}>\g<string></{0}>'.format(tag), self.text)

    def make_inline_element(self):
        # 사이트 내부 파일 처리
        self.text = re.sub('\[파일:(?P<file_name>.+?)(?<!mp3|txt|pdf)\]', '<img src="/file/\g<file_name>">', self.text)
        self.text = re.sub('\[파일:(?P<doc_name>.+)/(?P<file_name>.+?)\]', '<a href="/file/\g<doc_name>/\g<file_name>">\g<file_name></a>', self.text)
        # 사이트 외부 파일 처리
        # 글자 세부 옵션 처리

    # 관계가 없는 경우
    def make_index(self):
        string = '<div id="index"><span class="font_size_big">목차</span>'

        index_number = [0, 0, 0, 0, 0, 0]

        for h1_list in self.header:
            for h1_element in h1_list:
                if h1_list.index(h1_element) == 0:
                    index_number[0] = index_number[0] + 1
                    string = string + '<span><a href="#section{0}">{0}.</a> {subject}</span>'.format(index_number[0], subject=h1_element)
                else:
                    for h2_element in h1_element:
                        if h1_element.index(h2_element) == 0:
                            index_number[1] = index_number[1] + 1
                            string = string + '<span><a href="#section{0}.{1}">{0}.{1}.</a> {subject}</span>'\
                                .format(index_number[0], index_number[1], subject=h2_element)
                        else:
                            for h3_element in h2_element:
                                if h2_element.index(h3_element) == 0:
                                    index_number[2] = index_number[2] + 1
                                    string = string + '<span><a href="#section{0}.{1}.{2}">{0}.{1}.{2}.</a> {subject}</span>' \
                                        .format(index_number[0], index_number[1], index_number[2], subject=h3_element)
                                else:
                                    for h4_element in h3_element:
                                        if h3_element.index(h4_element) == 0:
                                            index_number[3] = index_number[3] + 1
                                            string = string + '<span><a href="#section{0}.{1}.{2}.{3}">{0}.{1}.{2}.{3}.</a> {subject}</span>' \
                                                .format(index_number[0], index_number[1], index_number[2],
                                                        index_number[3], subject=h4_element)
                                        else:
                                            for h5_element in h4_element:
                                                if h4_element.index(h5_element) == 0:
                                                    index_number[4] = index_number[4] + 1
                                                    string = string + '<span><a href="#section{0}.{1}.{2}.{3}.{4}">{0}.{1}.{2}.{3}.{4}.</a> {subject}</span>' \
                                                        .format(index_number[0], index_number[1], index_number[2],
                                                                index_number[3], index_number[4], subject=h5_element)
                                                else:
                                                    for h6_element in h5_element:
                                                        index_number[5] = index_number[5] + 1
                                                        string = string + '<span><a href="#section{0}.{1}.{2}.{3}.{4}.{5}">{0}.{1}.{2}.{3}.{4}.</a> {subject}</span>' \
                                                            .format(index_number[0], index_number[1], index_number[2],
                                                                    index_number[3], index_number[4], index_number[5],
                                                                    subject=h6_element)
            index_number = [index_number[0], 0, 0, 0, 0, 0]
        string += "</div>"
        return string

    def compile(self):
        # 줄 별로 처리해야 하는 메소드를 실행합니다.
        self.make_multiple_line('code', ':')
        self.make_multiple_line('blockquote', '>')

        self.make_header()
        self.make_block_element()
        self.make_list()
        self.make_table()
        self.make_link()

        # 처리된 줄들을 병합한 후, 한 번에 처리하는 메소드를 실행합니다.
        self.text = '<br>'.join(self.parted_text)

        # 한 번에 처리하는 메소도를 실행합니다.
        self.make_single_line('strong', '\*\*', '\*\*')
        self.make_single_line('del', '--', '--')
        self.make_single_line('em', '//', '//')
        self.make_single_line('sub', ',,', ',,')
        self.make_single_line('sup', '\^\^', '\^\^')

        self.make_inline_element()

        # 후처리를 합니다.
        self.text = re.sub('(?P<no_br></?h.>|</li>|</code>|</blockquote>)<br>', '\g<no_br>', self.text)
        self.text = re.sub('<br>(?P<no_br></?h.>)', '\g<no_br>', self.text)

        return self.text

