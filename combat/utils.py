import random
import requests
import time
import json
import logging

logger = logging.getLogger('django')


class MyDict(dict):

    def __init__(self, **kwargs):

        for k, v in self.__class__.__dict__.items():
            if not k.startswith('__'):
                self.__setattr__(k, kwargs.get(k, v))
        attrs = self.__dict__
        dict.__init__(self, **attrs)

    def __str__(self):
        return json.dumps(self)


class QuizData(MyDict):
    description = ''
    uid = ''
    title = ''
    status = ''
    difficulty = ''
    reward = 0


class SnippetData(MyDict):
    language = 'python3'
    body = ''
    run_count = 0
    contestant_id = -1
    quiz_id = -1
    status = ''
    uid = ''
    is_running = False


class EvaluateBase:
    # For subjects test
    # Success
    # {"response_code":0,"response_message":"pass","metrics":{"total":3,"error":0,"success":3}}

    # Syntax Error
    # {"response_code":1,"response_message":"syntax error","metrics":{"total":127,"error":127,"success":0}}

    # Fail
    # {"response_code":2,"response_message":"fail","metrics":{"total":0,"error":1,"success":0}}

    def eval(self, data):
        raise NotImplementedError


class SparkApiEvaluator(EvaluateBase):
    submit_url = 'http://35.198.254.175:3000/submit'
    timeout = 30  # sec
    code = {
        'error': 1,
        'fail': 2,
        'pass': 0,
        'start': -9,
        'finish': -10,
        'congrats': -1,
    }

    def eval(self, data):
        yield dict(
            response_code=self.code['start'],
            response_message='Start running tests. It would take about 15 seconds.',
            timestamp=time.time()
        )

        this_pass = False

        try:
            response = requests.post(self.submit_url, data=json.dumps(data), timeout=self.timeout)
            rdata = json.loads(response.content.decode('utf-8'))
            this_pass = rdata['response_code'] == 0
            yield dict(
                response_code=rdata['response_code'],
                response_message='[{}] detail: {}/{} testcases passed.'.format(
                    rdata['response_message'].upper(),
                    rdata['metrics']['success'],
                    rdata['metrics']['total']
                ),
                timestamp=time.time()  # TODO
            )
        except requests.ReadTimeout as err:
            logger.warning(err)
            yield dict(
                response_code=self.code['error'],
                response_message='Server timeout.',
                timestamp=time.time()
            )
        except Exception as err:
            logger.error(err)
            yield dict(
                response_code=self.code['error'],
                response_message='Unknown error occurred.',
                timestamp=time.time()
            )

        if this_pass:
            yield dict(
                response_code=self.code['congrats'],
                response_message='Congrats! You have passed this challenge.',
                timestamp=time.time()
            )

        yield dict(
            response_code=self.code['finish'],
            response_message='Finished.',
            timestamp=time.time()
        )


class PseudoEvaluator(EvaluateBase):

    template = {
        "response_code": 0,
        "response_message": "pass",
    }

    message = ['Pass', 'Syntax Error', 'Failed']

    def eval(self, data):
        yield dict(
            response_code=-9,
            response_message='Start running tests.',
            timestamp=time.time()
        )

        n_test = random.randint(3, 6)
        this_pass = True
        for i in range(n_test):
            time.sleep(0.1 + random.random() * 2)
            code = random.choice([0, 2])
            this_pass = this_pass and code == 0
            yield dict(
                response_code=code,
                response_message='Testcase {}: {}'.format(i + 1, self.message[code]),
                timestamp=time.time()
            )

        if this_pass:
            yield dict(
                response_code=-1,
                response_message='Congrats! You have passed this challenge.',
                timestamp=time.time()
            )

        yield dict(
            response_code=-10,
            response_message='Finished.',
            timestamp=time.time()
        )
